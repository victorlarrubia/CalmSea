# src/application/tools_definitions.py

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_resources",
            "description": "Lista recursos do Kubernetes (pods, services, deployments) em um namespace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["pods", "services", "deployments", "nodes"]},
                        "description": "Lista de tipos de recursos para buscar."
                    },
                    "namespace": {
                        "type": "string",
                        "description": "O namespace do Kubernetes (ex: 'default', 'kube-system')."
                    }
                },
                "required": ["resource_types", "namespace"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pod_logs",
            "description": "Retorna os logs (stdout) de um pod específico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {"type": "string", "description": "Nome exato do pod."},
                    "namespace": {"type": "string", "description": "Namespace onde o pod está."},
                    "tail_lines": {"type": "integer", "description": "Número de linhas finais para ler (padrão 50)."}
                },
                "required": ["pod_name", "namespace"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_namespaces",
            "description": "Lista todos os namespaces disponíveis no cluster.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
    # Podemos adicionar delete, apply, etc. depois
]