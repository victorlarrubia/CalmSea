# src/application/tools_definitions.py

SUPPORTED_RESOURCE_TYPES = [
    "pods",
    "services",
    "deployments",
    "configmaps",
    "secrets",
    "ingresses",
    "persistent_volume_claims",
    "replicasets",
    "statefulsets",
    "daemon_sets",
    "replication_controllers",
    "horizontal_pod_autoscalers",
    "jobs",
    "cronjobs",
    "namespaces",
    "nodes",
    "persistent_volumes",
]

RESOURCE_ALIASES_DESCRIPTION = (
    "Aliases aceitos pelo adapter: pod/po, service/svc, deployment/deploy, "
    "configmap/cm, ingress/ing, pvc, replicaset/rs, statefulset/sts, "
    "daemonset/ds, replicationcontroller/rc, horizontalpodautoscaler/hpa, "
    "cronjob/cj, namespace/ns, node/no, persistentvolume/pv."
)

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_resources",
            "description": (
                "Lista nomes de recursos Kubernetes de forma enxuta. "
                "Use esta ferramenta primeiro para descobrir quais recursos existem, "
                "antes de chamar get_resource_details. "
                "Aceita múltiplos tipos em uma única chamada para reduzir iterações. "
                f"{RESOURCE_ALIASES_DESCRIPTION}"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_types": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": SUPPORTED_RESOURCE_TYPES,
                        },
                        "description": (
                            "Lista de tipos de recursos para buscar. "
                            "Exemplo performático: ['pods', 'services', 'deployments']. "
                            "Evite buscar detalhes completos antes de listar os nomes."
                        ),
                    },
                    "namespace": {
                        "type": "string",
                        "description": (
                            "Namespace do Kubernetes. Para recursos cluster-wide, "
                            "como nodes, namespaces e persistent_volumes, o adapter "
                            "ignora o namespace quando necessário."
                        ),
                    },
                },
                "required": ["resource_types", "namespace"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_resource_details",
            "description": (
                "Obtém detalhes limpos de um recurso específico. "
                "Use somente depois de list_resources identificar o nome do recurso. "
                "O adapter remove metadados de runtime, como uid, resourceVersion, "
                "managedFields, creationTimestamp e status, reduzindo tokens enviados à LLM. "
                "Quando existir last-applied-configuration, o adapter prioriza esse manifesto."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "enum": SUPPORTED_RESOURCE_TYPES,
                        "description": (
                            "Tipo do recurso. Exemplos: pods, services, deployments, "
                            "configmaps, secrets, ingresses, jobs, cronjobs, hpa."
                        ),
                    },
                    "name": {
                        "type": "string",
                        "description": "Nome exato do recurso.",
                    },
                    "namespace": {
                        "type": "string",
                        "description": (
                            "Namespace do recurso. Para recursos cluster-wide, o adapter "
                            "ignora esse valor quando necessário."
                        ),
                    },
                },
                "required": ["resource_type", "name", "namespace"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pod_diagnostics",
            "description": (
                "Obtém diagnóstico estruturado de um pod específico. "
                "Use esta ferramenta quando um pod estiver Pending, ContainerCreating, "
                "CrashLoopBackOff, Error, ImagePullBackOff, ErrImagePull, "
                "CreateContainerConfigError ou quando o HealthCheck indicar timeout. "
                "Esta ferramenta reduz iterações porque retorna phase, conditions, "
                "container states, eventos, volumes referenciados, problemas detectados, "
                "causa raiz provável e ações recomendadas. "
                "É especialmente útil para detectar FailedMount, Secret inexistente, "
                "ConfigMap inexistente, falha de imagem e problemas de configuração."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {
                        "type": "string",
                        "description": (
                            "Nome exato do pod a diagnosticar. "
                            "Use list_resources com resource_types=['pods'] para descobrir o nome."
                        ),
                    },
                    "namespace": {
                        "type": "string",
                        "description": "Namespace onde o pod está.",
                    },
                    "tail_lines": {
                        "type": "integer",
                        "description": (
                            "Quantidade de linhas finais de log a tentar recuperar. "
                            "Padrão recomendado: 80. Se o container ainda não iniciou, "
                            "o adapter retornará a mensagem de indisponibilidade dos logs."
                        ),
                    },
                },
                "required": ["pod_name", "namespace"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pod_logs",
            "description": (
                "Retorna os logs de um pod específico. "
                "Use preferencialmente depois de get_pod_diagnostics quando o diagnóstico indicar "
                "CrashLoopBackOff, Error ou falha da aplicação. "
                "Para Pending, ContainerCreating e FailedMount, get_pod_diagnostics costuma ser melhor "
                "porque eventos e volumes são mais relevantes do que logs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {
                        "type": "string",
                        "description": "Nome exato do pod.",
                    },
                    "namespace": {
                        "type": "string",
                        "description": "Namespace onde o pod está.",
                    },
                    "tail_lines": {
                        "type": "integer",
                        "description": "Quantidade de linhas finais de log. Padrão recomendado: 80.",
                    },
                },
                "required": ["pod_name", "namespace"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_namespaces",
            "description": (
                "Lista namespaces disponíveis no cluster. "
                "Use quando o namespace correto não estiver claro. "
                "Namespaces de sistema podem ser omitidos pelo adapter para reduzir ruído."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_resource",
            "description": (
                "Remove um recurso específico do cluster. "
                "Ação destrutiva. Use apenas quando a remoção for necessária para corrigir "
                "um cenário ou limpar recurso quebrado. Não use para recursos de sistema."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "enum": SUPPORTED_RESOURCE_TYPES,
                        "description": "Tipo do recurso a remover.",
                    },
                    "name": {
                        "type": "string",
                        "description": "Nome exato do recurso a remover.",
                    },
                    "namespace": {
                        "type": "string",
                        "description": (
                            "Namespace do recurso. Para recursos cluster-wide, o adapter "
                            "ignora esse valor quando necessário."
                        ),
                    },
                },
                "required": ["resource_type", "name", "namespace"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scale_resource",
            "description": (
                "Altera o número de réplicas de um recurso escalável. "
                "Suporta principalmente deployments, statefulsets e replication_controllers, "
                "conforme configuração do resource_config.yaml."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "enum": [
                            "deployments",
                            "statefulsets",
                            "replication_controllers",
                        ],
                        "description": "Tipo do recurso escalável.",
                    },
                    "name": {
                        "type": "string",
                        "description": "Nome exato do recurso escalável.",
                    },
                    "replicas": {
                        "type": "integer",
                        "description": "Novo número de réplicas desejado.",
                    },
                    "namespace": {
                        "type": "string",
                        "description": "Namespace do recurso.",
                    },
                },
                "required": ["resource_type", "name", "replicas", "namespace"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply_manifest",
            "description": (
                "Aplica um manifesto Kubernetes corrigido no cluster. "
                "Suporta YAML string, YAML multi-documento separado por '---', ou JSON serializável. "
                "O adapter executa limpeza de metadados e dry-run server-side antes do apply real. "
                "Use uma única chamada com manifesto multi-documento quando precisar aplicar vários recursos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "manifest": {
                        "type": "string",
                        "description": (
                            "Conteúdo YAML completo, limpo e corrigido. "
                            "Não inclua campos de runtime como uid, resourceVersion, managedFields, "
                            "creationTimestamp ou status. "
                            "Para múltiplos recursos, use YAML multi-documento separado por '---'."
                        ),
                    },
                    "namespace": {
                        "type": "string",
                        "description": (
                            "Namespace alvo. Para manifestos com recursos cluster-wide, "
                            "o adapter remove o argumento de namespace quando necessário."
                        ),
                    },
                },
                "required": ["manifest", "namespace"],
            },
        },
    },
]