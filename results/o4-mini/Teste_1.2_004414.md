# Teste 1-orion.yaml - Rep 2

## Análise
Segue a lista de problemas e inconsistências detectados no seu manifesto:

1. Credenciais hard-coded  
   - DB_PASSWORD e API_KEY estão expostos em variáveis de ambiente.  
   - Usuário e senha do Mongo (“-dbuser … -dbpwd 123456789”) também estão em clear text nos args.  
   → Use Kubernetes Secrets e `secretKeyRef`.

2. Imagem sem tag fixa  
   - `image: fiware/orion-ld` implicita o tag “latest”.  
   → Sempre pinagem de versão (ex.: `:3.0.0-rc1`) e defina `imagePullPolicy: Always`.

3. Service selector incorreto  
   - Deployment marca pods com label `app: orionld`, mas o Service usa `selector: app: orionlds`.  
   → Corrija para o mesmo label (`orionld`).

4. Ausência de securityContext  
   - Não há restrições de usuário (runAsNonRoot), capabilities, SELinux ou AppArmor.  
   → Defina `securityContext` no Pod/Container para rodar como usuário não-root e dropar privilégios.

5. imagePullPolicy padrão  
   - Sem declaração, o Kubernetes usa `IfNotPresent`, o que pode mascarar versões antigas na cache.  
   → Explícito `Always` em produção.

6. Exposição pública irrestrita  
   - Service `type: LoadBalancer` sem NetworkPolicy ou Firewall pode abrir sua API ao mundo.  
   → Considere `ClusterIP` + Ingress com regras ou NetworkPolicies para limitar o acesso.

7. Falta de NetworkPolicy  
   - Sem políticas de rede, qualquer pod no cluster pode conversar com seu Orion-LD.  
   → Adicione NetworkPolicies permitindo somente fontes / destinos autorizados.

8. Sem PodDisruptionBudget  
   - Não há PDB para garantir disponibilidade mínima do Deployment durante manutenções ou upgrades.  
   → Defina um PDB (e.g. minAvailable: 2).

9. HPA sem garantia de métricas  
   - Uso de autoscaling/v2 com métricas de CPU e memória exige metrics-server ou Prometheus Adapter corretamente instalado.  
   → Verifique se o cluster fornece esses metrics endpoints.

10. Template.metadata.name redundante  
    - `template.metadata.name: fiware-orion` não é usado em matching e pode confundir suas ferramentas de CI/CD.  
    → Remova ou alinhe com `metadata.name` do Deployment.

Recomendações gerais:  
- Coloque esse Deployment em um Namespace dedicado com limites de quotas.  
- Use RBAC restritivo para quem pode criar/alterar esses recursos.  
- Aplique scanners de imagem (e.g. Trivy) e políticas de admissão (OPA Gatekeeper) para reforçar compliance.

## Fix
✅ **Executado apply_manifest:**

```json
🚀 **Aplicado:** {'status': 'success', 'message': 'Sucesso:\ndeployment.apps/fiware-orionld configured\nservice/fiware-orionld-service configured\nhorizontalpodautoscaler.autoscaling/fiware-orionld-hpa unchanged\n'}
```

## K8s
```
NAME                              READY   STATUS              RESTARTS   AGE
fiware-orionld-548584cdf-2sx47    0/1     Running             0          35s
fiware-orionld-548584cdf-f5cvm    0/1     Running             0          35s
fiware-orionld-548584cdf-z4l85    0/1     Running             0          35s
fiware-orionld-7b6c94fbf7-xsqt6   0/1     ContainerCreating   0          0s
```