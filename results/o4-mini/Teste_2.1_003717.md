# Teste 2-frontend.yaml - Rep 1

## Análise
Segue a lista de problemas de segurança e boas práticas ausentes neste Deployment:

1. Imagem incorreta/sem verificação (“nginxs”)  
   - Nome sintaticamente inválido e sem tag (latest por padrão).  
   - Sem referência a digest ou tag imutável, dificulta rastrear e reproduzir.  
   - Sem scanner de vulnerabilidades integrado.

2. Credenciais em clear-text  
   - `PASSWORD_SERVICE_HOST: "123456"` está hard-coded no spec.  
   - Deve usar Secret (e montar como envFrom ou volume) ou CSI Secrets Store.

3. Falta de isolamento de privilégios  
   - Ausência de `securityContext` (pod e container).  
     • Não há `runAsNonRoot: true` nem `runAsUser`/`runAsGroup`.  
     • Sem `allowPrivilegeEscalation: false`.  
     • Sem `capabilities.drop: ["ALL"]` (e re-adicionar só as necessárias).

4. Ausência de limites de recursos  
   - Apenas “requests” configurados; falta `limits.cpu` e `limits.memory`.  
   - Sem limites, container pode consumir toda a cota do nó e afetar outros workloads.

5. Sem probes de liveness/readiness  
   - Executar sem `readinessProbe` e `livenessProbe` aumenta janela de indisponibilidade e dificulta rolling updates.

6. Rede sem restrição  
   - Nenhum NetworkPolicy atrelado; o pod poderá ser alcançado por qualquer fonte no namespace (ou mesmo externamente, se não houver Ingress/Firewall).

7. ServiceAccount padrão e RBAC genérico  
   - Não foi definido `serviceAccountName`, então em uso está o default, possivelmente com permissões excessivas.

8. Logging, Monitoring e Audit  
   - Sem sidecar ou configurações de coleta (Fluentd, Prometheus exposers) para capturar métricas, logs estruturados e eventos de segurança.

Recomendações resumidas:  
- Corrigir nome da imagem, usar tag imutável e integrar scanner de vulnerabilidades.  
- Extrair credenciais para Secrets.  
- Habilitar `securityContext` rigoroso (runAsNonRoot, dropCapabilities, seccomp, etc.).  
- Definir requests *e* limits.  
- Adicionar probes de liveness/readiness.  
- Implementar NetworkPolicies e um ServiceAccount com menores privilégios.  
- Incluir mecanismo de logging/agregação e monitoramento.

## Fix
✅ **Executado apply_manifest:**

```json
🚀 **Aplicado:** {'status': 'success', 'message': 'Sucesso:\ndeployment.apps/frontend configured\n'}
```

## K8s
```
NAME                        READY   STATUS              RESTARTS   AGE
frontend-65d44dd469-fzgt4   0/1     ImagePullBackOff    0          25s
frontend-6dfbcddc4-nrjng    0/1     ContainerCreating   0          0s
```