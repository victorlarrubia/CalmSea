# Roteiro AWS - Benchmark completo AgentK++ / CalmSea

Repositorio: https://github.com/victorlarrubia/CalmSea  
Branch principal: master

## Objetivo

Rodar, na instancia EC2 com Ollama e GPU, os testes completos do AgentK++ com os tres modelos alvo. Cada modelo deve executar os 10 YAMLs, com 5 repeticoes por YAML. Ao final, os resultados dos tres modelos devem ser enviados juntos para o GitHub na pasta results.

## Modelos alvo

| Modelo | Parametros | num_ctx |
|---|---:|---:|
| qwen3-coder:30b-a3b-q4_K_M | 30,5B | 16384 |
| mistral-small3.2:24b-instruct-2506-q4_K_M | 24B | 24576 |
| qwen3.5:27b-q4_K_M | 27B | 24576 |

## Configuracao padrao

AGENTK_MAX_HISTORY_MESSAGES=10  
AGENTK_MAX_TOOL_RESULT_CHARS=1600  
AGENTK_MAX_LOG_CHARS=800

## Instancias AWS

AgentK++ / Ollama:
- Name: AgentK++v1.3.1-Ollama
- Instance ID: i-008a1cf8204703910
- Type: g6.2xlarge
- Region: us-east-1
- SSH Host: AgentK++v1.3.1-Ollama

Minikube:
- Name: minikube2
- Instance ID: i-00746782c80ae41f8
- Type: t3.large
- Region: us-east-1
- SSH Host: minikube2

## Preparacao na EC2

1. Acessar a instancia AgentK++v1.3.1-Ollama por SSH ou Remote SSH do VS Code.
2. Atualizar o repositorio:

cd ~  
git clone https://github.com/victorlarrubia/CalmSea.git 2>/dev/null || true  
cd CalmSea  
git checkout master  
git pull origin master

3. Revisar o arquivo .env:

cp .env.example .env 2>/dev/null || true  
nano .env

Verificar variaveis de Ollama, kubeconfig, certificados, acesso ao Minikube e configuracoes usadas pelo docker compose.

## Validacao antes dos testes

Rodar:

python -m py_compile src/application/services/agent_service.py src/application/history_compaction/history_compactor_service.py src/application/next_action/next_action_policy.py src/application/tool_call_recovery/tool_call_recovery_service.py src/infrastructure/k8s_adapter/health_checker.py src/performance_test/main.py

docker compose --env-file .env run --rm tests-unit

Resultado esperado: 15 passed.

## Rodar os tres modelos

Executar:

COMPOSE_PROFILE=nvidia OLLAMA_SERVICE=ollama REPS=5 BENCHMARK_TIMEOUT=900m ./scripts/aws/run_all_target_models_aws.sh

O script limpa results uma unica vez no inicio e acumula os resultados dos tres modelos.

## Gerar resumo

python3 scripts/aws/summarize_benchmark_results.py results

## Arquivar resultados

mkdir -p local_archives/final_results  
tar -czf "local_archives/final_results/results_all_target_models_$(date +%Y%m%d_%H%M%S).tar.gz" results

## Subir resultados ao GitHub

Depois que os tres modelos terminarem:

git status --short  
git add results  
git commit -m "results: add final AWS benchmark results for target Ollama models"  
git push origin master

## Observacoes

- A pasta results nao deve estar no .gitignore.
- Os resultados dos tres modelos devem subir juntos em um unico commit.
- O script run_full_benchmark_aws.sh aceita CLEAN_RESULTS=false.
- O script run_all_target_models_aws.sh ja usa CLEAN_RESULTS=false para preservar os resultados entre modelos.
- Usar nvidia-smi e ollama ps para validar o uso da GPU.