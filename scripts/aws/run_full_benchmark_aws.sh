#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:-}"
REPS="${REPS:-5}"
COMPOSE_PROFILE="${COMPOSE_PROFILE:-nvidia}"
OLLAMA_SERVICE="${OLLAMA_SERVICE:-ollama}"
BENCHMARK_TIMEOUT="${BENCHMARK_TIMEOUT:-900m}"
CLEAN_RESULTS="${CLEAN_RESULTS:-true}"

YAMLS="${YAMLS:-1-orion.yaml,2-frontend.yaml,3-mysql.yaml,4-vllm.yaml,5-nginx.yaml,6-selenium.yaml,7-elasticsearch.yaml,8-newrelic.yaml,9-storm.yaml,10-mongodb.yaml}"

AGENTK_MAX_HISTORY_MESSAGES="${AGENTK_MAX_HISTORY_MESSAGES:-10}"
AGENTK_MAX_TOOL_RESULT_CHARS="${AGENTK_MAX_TOOL_RESULT_CHARS:-1600}"
AGENTK_MAX_LOG_CHARS="${AGENTK_MAX_LOG_CHARS:-800}"

if [ -z "$MODEL" ]; then
  echo "Uso: ./scripts/aws/run_full_benchmark_aws.sh <modelo>"
  echo "Modelos alvo:"
  echo "  qwen3-coder:30b-a3b-q4_K_M"
  echo "  mistral-small3.2:24b-instruct-2506-q4_K_M"
  echo "  qwen3.5:27b-q4_K_M"
  exit 1
fi

case "$MODEL" in
  "qwen3-coder:30b-a3b-q4_K_M")
    export OLLAMA_NUM_CTX="${OLLAMA_NUM_CTX:-16384}"
    ;;
  "mistral-small3.2:24b-instruct-2506-q4_K_M")
    export OLLAMA_NUM_CTX="${OLLAMA_NUM_CTX:-24576}"
    ;;
  "qwen3.5:27b-q4_K_M")
    export OLLAMA_NUM_CTX="${OLLAMA_NUM_CTX:-24576}"
    ;;
  *)
    export OLLAMA_NUM_CTX="${OLLAMA_NUM_CTX:-24576}"
    echo "AVISO: modelo fora da tabela alvo. Usando OLLAMA_NUM_CTX=$OLLAMA_NUM_CTX."
    ;;
esac

echo "===== CONFIGURAÇÃO DO BENCHMARK ====="
echo "MODEL=$MODEL"
echo "REPS=$REPS"
echo "YAMLS=$YAMLS"
echo "COMPOSE_PROFILE=$COMPOSE_PROFILE"
echo "OLLAMA_SERVICE=$OLLAMA_SERVICE"
echo "OLLAMA_NUM_CTX=$OLLAMA_NUM_CTX"
echo "AGENTK_MAX_HISTORY_MESSAGES=$AGENTK_MAX_HISTORY_MESSAGES"
echo "AGENTK_MAX_TOOL_RESULT_CHARS=$AGENTK_MAX_TOOL_RESULT_CHARS"
echo "AGENTK_MAX_LOG_CHARS=$AGENTK_MAX_LOG_CHARS"
echo "CLEAN_RESULTS=$CLEAN_RESULTS"

PROFILE_ARGS=()
if [ "$COMPOSE_PROFILE" != "none" ]; then
  PROFILE_ARGS=(--profile "$COMPOSE_PROFILE")
fi

echo
echo "===== VALIDANDO .ENV ====="
if [ ! -f .env ]; then
  echo "ERRO: arquivo .env não encontrado."
  exit 1
fi

echo
echo "===== SUBINDO OLLAMA ====="
docker compose "${PROFILE_ARGS[@]}" --env-file .env up -d "$OLLAMA_SERVICE"

echo
echo "===== AGUARDANDO OLLAMA RESPONDER ====="
for i in $(seq 1 60); do
  if curl -s http://127.0.0.1:11434/api/tags >/dev/null; then
    echo "Ollama respondeu na tentativa $i"
    break
  fi
  echo "Aguardando Ollama... tentativa $i"
  sleep 2
done

echo
echo "===== BAIXANDO/VALIDANDO MODELO ====="
docker compose "${PROFILE_ARGS[@]}" --env-file .env exec -T "$OLLAMA_SERVICE" ollama pull "$MODEL"

echo
echo "===== MODELOS DISPONÍVEIS ====="
curl -s http://127.0.0.1:11434/api/tags | python3 -m json.tool | grep -E "$MODEL|name|model" || true

echo
echo "===== PREPARANDO RESULTS DA RODADA ====="
if [ "$CLEAN_RESULTS" = "true" ]; then
  echo "Limpando results antes da rodada."
  rm -rf results
  mkdir -p results
else
  echo "Mantendo results existente para acumular resultados de múltiplos modelos."
  mkdir -p results
fi

echo
echo "===== REMOVENDO CONTAINER ANTIGO DO PERFORMANCE TEST ====="
docker compose "${PROFILE_ARGS[@]}" --env-file .env rm -sf performancetest >/dev/null 2>&1 || true

echo
echo "===== INÍCIO DO BENCHMARK COMPLETO ====="
date "+%Y-%m-%d %H:%M:%S"

mkdir -p local_archives/logs

set -o pipefail

timeout "$BENCHMARK_TIMEOUT" docker compose "${PROFILE_ARGS[@]}" --env-file .env run --rm \
  --user "$(id -u):$(id -g)" \
  -e PERFORMANCE_TEST_MODELS="$MODEL" \
  -e PERFORMANCE_TEST_REPS="$REPS" \
  -e PERFORMANCE_TEST_YAMLS="$YAMLS" \
  -e PERFORMANCE_TEST_SLEEP_SECONDS="${PERFORMANCE_TEST_SLEEP_SECONDS:-2}" \
  -e AGENTK_MAX_HISTORY_MESSAGES="$AGENTK_MAX_HISTORY_MESSAGES" \
  -e AGENTK_MAX_TOOL_RESULT_CHARS="$AGENTK_MAX_TOOL_RESULT_CHARS" \
  -e AGENTK_MAX_LOG_CHARS="$AGENTK_MAX_LOG_CHARS" \
  -e AGENTK_EARLY_HEALTHCHECK_TIMEOUT="${AGENTK_EARLY_HEALTHCHECK_TIMEOUT:-180}" \
  -e AGENTK_HEALTH_STABLE_SUCCESS_POLLS="${AGENTK_HEALTH_STABLE_SUCCESS_POLLS:-2}" \
  -e AGENTK_HEALTH_POLL_INTERVAL_SECONDS="${AGENTK_HEALTH_POLL_INTERVAL_SECONDS:-5}" \
  -e AGENTK_HEALTH_FAILED_POD_STORM_THRESHOLD="${AGENTK_HEALTH_FAILED_POD_STORM_THRESHOLD:-8}" \
  -e OLLAMA_NUM_CTX="$OLLAMA_NUM_CTX" \
  performancetest | tee "local_archives/logs/benchmark_${MODEL//[:\/]/_}_$(date +%Y%m%d_%H%M%S).log"

EXIT_CODE=${PIPESTATUS[0]}

echo
echo "===== FIM DO BENCHMARK COMPLETO ====="
date "+%Y-%m-%d %H:%M:%S"
echo "EXIT_CODE=$EXIT_CODE"

exit "$EXIT_CODE"