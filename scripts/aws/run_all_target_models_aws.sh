#!/usr/bin/env bash
set -euo pipefail

MODELS=(
  "qwen3-coder:30b-a3b-q4_K_M"
  "mistral-small3.2:24b-instruct-2506-q4_K_M"
  "qwen3.5:27b-q4_K_M"
)

REPS="${REPS:-5}"
COMPOSE_PROFILE="${COMPOSE_PROFILE:-nvidia}"
OLLAMA_SERVICE="${OLLAMA_SERVICE:-ollama}"
BENCHMARK_TIMEOUT="${BENCHMARK_TIMEOUT:-900m}"

AGENTK_MAX_HISTORY_MESSAGES="${AGENTK_MAX_HISTORY_MESSAGES:-10}"
AGENTK_MAX_TOOL_RESULT_CHARS="${AGENTK_MAX_TOOL_RESULT_CHARS:-1600}"
AGENTK_MAX_LOG_CHARS="${AGENTK_MAX_LOG_CHARS:-800}"

echo "===== CONFIGURAÇÃO DA BATERIA COMPLETA AWS ====="
echo "REPS=$REPS"
echo "COMPOSE_PROFILE=$COMPOSE_PROFILE"
echo "OLLAMA_SERVICE=$OLLAMA_SERVICE"
echo "BENCHMARK_TIMEOUT=$BENCHMARK_TIMEOUT"
echo "AGENTK_MAX_HISTORY_MESSAGES=$AGENTK_MAX_HISTORY_MESSAGES"
echo "AGENTK_MAX_TOOL_RESULT_CHARS=$AGENTK_MAX_TOOL_RESULT_CHARS"
echo "AGENTK_MAX_LOG_CHARS=$AGENTK_MAX_LOG_CHARS"

echo
echo "===== LIMPANDO RESULTS UMA ÚNICA VEZ ANTES DOS 3 MODELOS ====="
rm -rf results
mkdir -p results

mkdir -p local_archives/logs
mkdir -p local_archives/final_results

START_TS="$(date +%Y%m%d_%H%M%S)"

for MODEL in "${MODELS[@]}"; do
  echo
  echo "================================================================"
  echo "===== INICIANDO MODELO: $MODEL"
  echo "================================================================"

  CLEAN_RESULTS=false \
  REPS="$REPS" \
  COMPOSE_PROFILE="$COMPOSE_PROFILE" \
  OLLAMA_SERVICE="$OLLAMA_SERVICE" \
  BENCHMARK_TIMEOUT="$BENCHMARK_TIMEOUT" \
  AGENTK_MAX_HISTORY_MESSAGES="$AGENTK_MAX_HISTORY_MESSAGES" \
  AGENTK_MAX_TOOL_RESULT_CHARS="$AGENTK_MAX_TOOL_RESULT_CHARS" \
  AGENTK_MAX_LOG_CHARS="$AGENTK_MAX_LOG_CHARS" \
  ./scripts/aws/run_full_benchmark_aws.sh "$MODEL"

  echo
  echo "===== RESUMO PARCIAL APÓS $MODEL ====="
  python3 scripts/aws/summarize_benchmark_results.py results || true
done

echo
echo "===== RESUMO FINAL DOS 3 MODELOS ====="
python3 scripts/aws/summarize_benchmark_results.py results | tee "local_archives/logs/summary_all_models_${START_TS}.md"

echo
echo "===== ARQUIVANDO RESULTS FINAL DOS 3 MODELOS ====="
tar -czf "local_archives/final_results/results_all_target_models_${START_TS}.tar.gz" results

echo
echo "===== STATUS GIT APÓS BATERIA COMPLETA ====="
git status --short

echo
echo "===== PRÓXIMO PASSO MANUAL PARA SUBIR RESULTS ====="
echo "git add results"
echo "git commit -m \"results: add final AWS benchmark results for target Ollama models\""
echo "git push origin master"