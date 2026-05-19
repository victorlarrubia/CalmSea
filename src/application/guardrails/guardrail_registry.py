from __future__ import annotations

from typing import Any, Iterable, List

from src.application.guardrails.base import ManifestGuardrail
from src.application.guardrails.elasticsearch_guardrail import ElasticsearchGuardrail
from src.application.guardrails.frontend_guardrail import FrontendGuardrail
from src.application.guardrails.models import GuardrailDecision
from src.application.guardrails.mongodb_guardrail import MongoDBGuardrail
from src.application.guardrails.newrelic_guardrail import NewRelicGuardrail
from src.application.guardrails.nginx_guardrail import NginxGuardrail
from src.application.guardrails.orion_guardrail import OrionGuardrail
from src.application.guardrails.storm_guardrail import StormGuardrail


class GuardrailRegistry:
    """
    Centraliza a execução dos guardrails de manifesto.

    Ordem importa:
    - Frontend antes de Nginx para impedir que manifestos my-nginx/nginxsvc inventados contaminem teste-frontend;
    - Nginx continua antes dos demais cenários para capturar o caso 5-nginx.yaml;
    - Orion antes de MongoDB, porque o manifesto Orion contém MongoDB interno;
    - MongoDB depois de Orion para evitar capturar orionld-mongodb.
    """

    def __init__(self, guardrails: Iterable[ManifestGuardrail] | None = None):
        self.guardrails: List[ManifestGuardrail] = list(
            guardrails
            if guardrails is not None
            else [
                FrontendGuardrail(),
                NginxGuardrail(),
                OrionGuardrail(),
                MongoDBGuardrail(),
                StormGuardrail(),
                NewRelicGuardrail(),
                ElasticsearchGuardrail(),
            ]
        )

    def evaluate(self, manifest: Any, namespace: str) -> GuardrailDecision:
        for guardrail in self.guardrails:
            decision = guardrail.evaluate(manifest=manifest, namespace=namespace)

            if decision.matched:
                return decision

        return GuardrailDecision(matched=False)
