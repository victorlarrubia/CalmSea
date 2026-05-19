from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List, Set

from src.application.tool_call_recovery.tool_call_recovery_models import (
    ToolCallRecoveryDecision,
)


class ToolCallRecoveryService:
    """
    Detecta respostas textuais que deveriam ser tool calls.

    Esta camada é propositalmente conservadora:
    - não autoexecuta ferramentas extraídas do texto;
    - não interpreta YAML livre como comando confiável;
    - apenas bloqueia respostas textuais que afirmam execução de ferramenta
      sem uma chamada real correspondente.

    Fica na camada application porque representa regra de orquestração do agente,
    não infraestrutura.
    """

    TOOL_ALIASES = {
        "list_resources": [
            "list_resources",
            "listar recursos",
            "listei recursos",
            "listando recursos",
        ],
        "get_resource_details": [
            "get_resource_details",
            "resource_details",
            "detalhes do recurso",
            "obter detalhes",
            "obtendo detalhes",
        ],
        "get_pod_diagnostics": [
            "get_pod_diagnostics",
            "pod_diagnostics",
            "diagnostico do pod",
            "diagnóstico do pod",
            "diagnosticar pod",
        ],
        "get_pod_logs": [
            "get_pod_logs",
            "pod logs",
            "logs do pod",
            "ler logs",
        ],
        "apply_manifest": [
            "apply_manifest",
            "apply manifest",
            "aplicar manifesto",
            "aplicando manifesto",
            "apliquei manifesto",
            "manifesto aplicado",
            "kubectl apply",
        ],
        "delete_resource": [
            "delete_resource",
            "deletar recurso",
            "deletando recurso",
            "remover recurso",
            "removi recurso",
            "delete resource",
        ],
        "scale_resource": [
            "scale_resource",
            "escalar recurso",
            "scale resource",
        ],
        # Não é ferramenta pública no schema, mas aparece muito em respostas
        # textuais como alucinação de execução.
        "check_health": [
            "check_health",
            "healthcheck",
            "health check",
            "verificar saúde",
            "verificando saúde",
        ],
    }

    EXECUTION_VERBS = [
        "executei",
        "executando",
        "executo",
        "vou executar",
        "chamei",
        "chamando",
        "vou chamar",
        "usei",
        "usando",
        "apliquei",
        "aplicando",
        "aplicar",
        "aplicado",
        "rodei",
        "rodando",
        "running",
        "ran",
        "called",
        "calling",
        "applied",
        "apply",
    ]

    NEGATION_MARKERS = [
        "nao executei",
        "não executei",
        "nao foi executado",
        "não foi executado",
        "sem executar",
        "nao vou executar",
        "não vou executar",
        "não apliquei",
        "nao apliquei",
    ]

    def evaluate_reply(
        self,
        content: str,
        actually_executed_tools: Iterable[str] | None = None,
    ) -> ToolCallRecoveryDecision:
        """
        Avalia uma resposta textual da LLM.

        Deve ser chamado somente quando a decisão da LLM vier como action="reply".
        Se a LLM realmente retornou action="parallel_tool_use", esta camada não
        deve interferir.
        """
        text = str(content or "").strip()

        if not text:
            return ToolCallRecoveryDecision(should_block=False)

        normalized_text = self._normalize(text)
        actually_executed = {
            self._normalize_tool_name(tool_name)
            for tool_name in (actually_executed_tools or [])
        }

        detected_tool_names, detected_patterns = self._detect_tool_execution_claims(
            text=text,
            normalized_text=normalized_text,
        )

        if self._looks_like_freeform_manifest_execution(text, normalized_text):
            detected_tool_names.add("apply_manifest")
            detected_patterns.append("freeform_manifest_execution")

        if not detected_tool_names:
            return ToolCallRecoveryDecision(should_block=False)

        if self._is_clear_negation(normalized_text) and not self._looks_like_freeform_manifest_execution(text, normalized_text):
            return ToolCallRecoveryDecision(should_block=False)

        # check_health não é tool pública de LLM; a verificação de saúde é interna
        # após apply_manifest. Se o modelo declarar essa chamada, deve ser corrigido.
        invalid_or_missing = {
            tool_name
            for tool_name in detected_tool_names
            if tool_name == "check_health" or tool_name not in actually_executed
        }

        if not invalid_or_missing:
            return ToolCallRecoveryDecision(should_block=False)

        detected_sorted = sorted(detected_tool_names)
        missing_sorted = sorted(invalid_or_missing)
        executed_sorted = sorted(actually_executed)

        corrective_message = self._build_corrective_message(
            detected_tool_names=detected_sorted,
            missing_tool_names=missing_sorted,
            actually_executed_tools=executed_sorted,
        )

        return ToolCallRecoveryDecision(
            should_block=True,
            reason=(
                "Resposta textual afirma execução ou intenção de ferramenta sem "
                "tool call real correspondente."
            ),
            detected_tool_names=detected_sorted,
            detected_patterns=sorted(set(detected_patterns)),
            corrective_message=corrective_message,
            confidence="high",
        )

    def _detect_tool_execution_claims(
        self,
        text: str,
        normalized_text: str,
    ) -> tuple[Set[str], List[str]]:
        detected_tool_names: Set[str] = set()
        detected_patterns: List[str] = []

        for canonical_tool_name, aliases in self.TOOL_ALIASES.items():
            for alias in aliases:
                normalized_alias = self._normalize(alias)

                for match in re.finditer(re.escape(normalized_alias), normalized_text):
                    start = max(0, match.start() - 90)
                    end = min(len(normalized_text), match.end() + 60)
                    window = normalized_text[start:end]

                    if self._contains_execution_verb(window):
                        detected_tool_names.add(canonical_tool_name)
                        detected_patterns.append(f"execution_claim:{canonical_tool_name}")
                        break

        # Frases sem o nome apply_manifest, mas com alegação clara de manifesto aplicado.
        manifest_claim_patterns = [
            "executei o manifesto",
            "executando o manifesto",
            "apliquei o manifesto",
            "aplicando o manifesto",
            "manifesto aplicado",
            "aplicacao do manifesto",
            "aplicação do manifesto",
        ]

        for pattern in manifest_claim_patterns:
            if self._normalize(pattern) in normalized_text:
                detected_tool_names.add("apply_manifest")
                detected_patterns.append("manifest_execution_claim")

        return detected_tool_names, detected_patterns

    def _looks_like_freeform_manifest_execution(
        self,
        text: str,
        normalized_text: str,
    ) -> bool:
        has_yaml_shape = (
            "apiversion:" in normalized_text
            and "kind:" in normalized_text
            and (
                "metadata:" in normalized_text
                or "spec:" in normalized_text
            )
        )

        if not has_yaml_shape:
            return False

        execution_or_apply_intent = (
            "apply_manifest" in normalized_text
            or "kubectl apply" in normalized_text
            or "executei" in normalized_text
            or "executando" in normalized_text
            or "apliquei" in normalized_text
            or "aplicando" in normalized_text
            or "aplicar" in normalized_text
            or "aplicacao" in normalized_text
            or "aplicação" in normalized_text
        )

        return execution_or_apply_intent

    def _contains_execution_verb(self, normalized_window: str) -> bool:
        return any(
            self._normalize(verb) in normalized_window
            for verb in self.EXECUTION_VERBS
        )

    def _is_clear_negation(self, normalized_text: str) -> bool:
        return any(
            self._normalize(marker) in normalized_text
            for marker in self.NEGATION_MARKERS
        )

    def _build_corrective_message(
        self,
        detected_tool_names: List[str],
        missing_tool_names: List[str],
        actually_executed_tools: List[str],
    ) -> str:
        primary_tool = missing_tool_names[0] if missing_tool_names else "ferramenta_necessaria"

        return (
            "[SISTEMA]: Resposta bloqueada pelo ToolCallRecovery. "
            f"Ferramenta requerida: {primary_tool}. "
            "Responda somente com action='parallel_tool_use' e a tool call correta. "
            "Não escreva YAML em texto livre. "
            "Não declare check_health; HealthCheck é interno após apply_manifest."
        )

    def _normalize_tool_name(self, tool_name: str) -> str:
        return str(tool_name or "").strip()

    def _normalize(self, value: str) -> str:
        text = str(value or "").lower()

        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))

        text = re.sub(r"\s+", " ", text)

        return text.strip()
