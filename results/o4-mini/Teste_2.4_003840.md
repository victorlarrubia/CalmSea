# Teste 2-frontend.yaml - Rep 4

## Análise
Segue a lista de problemas e más práticas encontradas neste Deployment:

1. Imagem mal especificada e sem versão fixa  
   - Usou “nginxs” (provável typo) em vez de “nginx”  
   - Não há tag ou digest (usa `:latest` por padrão) – dificulta reprodutibilidade e pode introduzir mudanças inesperadas

2. Variável sensível exposta em plain-text  
   - `PASSWORD_SERVICE_HOST: "123456"` está hard-coded no spec  
   - Dados sensíveis devem ser referenciados via Kubernetes Secret, não em `env`

3. Ausência de probes de saúde  
   - Não há liveness nem readiness probes  
   - Pod pode ficar “pronto” mesmo que o serviço interno tenha travado

4. Recursos sem limites definidos  
   - Só há `requests` de CPU/memória, mas faltam `limits`  
   - Sem `limits`, um pod mal-comportado pode causar OOM ou “noisy neighbor”

5. Sem securityContext nem PodSecurityContext  
   - Container roda como root (UID 0) por padrão  
   - Falta de:  
     • runAsNonRoot/runAsUser  
     • dropCapabilities  
     • readOnlyRootFilesystem  
     • seccompProfile

6. Usa ServiceAccount default  
   - Sem ServiceAccount dedicado nem regras RBAC mínimas  
   - Se invadir o pod, atacante ganha permissões do default no namespace

7. Ausência de NetworkPolicy  
   - Não há restrição de tráfego de entrada/saída para o pod  
   - Facilita movimentos laterais em caso de comprometimento

8. Replica única  
   - `replicas: 1` em produção gera ponto único de falha  
   - Recomenda-se ao menos 2 réplicas para alta disponibilidade

9. Falta de políticas de afinidade/anti-afinidade  
   - Nada garante espalhamento dos pods nem tolerância a falhas de nó

10. imagePullPolicy implícita  
   - Não declarado (`IfNotPresent` para tags fixas, `Always` para `:latest`)  
   - Pode causar pulls inesperados ou não atualizar quando desejado

Todos esses pontos devem ser corrigidos para ter um Deployment mais seguro, estável e previsível em produção.

## Fix
✅ **Executado apply_manifest:**

```json
🚀 **Aplicado:** {'status': 'success', 'message': 'Sucesso:\ndeployment.apps/frontend configured\n'}
```

## K8s
```
NAME                        READY   STATUS              RESTARTS   AGE
frontend-65d44dd469-r5rbr   0/1     ImagePullBackOff    0          23s
frontend-685f94c7c5-zhl8w   0/1     ContainerCreating   0          0s
```