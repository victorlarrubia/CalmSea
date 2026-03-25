# Teste 1-orion.yaml - Rep 4

## Análise
Segue a lista de problemas e más práticas identificadas no manifesto:

1. Secrets hard-coded  
   - Senhas e chaves (DB_PASSWORD, API_KEY e o `-dbpwd` nos args) estão em texto plano.  
   - Devem ser armazenados em Objetos Secret do K8s e referenciados via `envFrom` ou `env.valueFrom.secretKeyRef`.

2. Seletores inconsistentes  
   - Deployment usa label `app: orionld`  
   - Service busca `app: orionlds` (note o “s” extra).  
   - Com isso, o Service não irá encaminhar tráfego para nenhum Pod.

3. Imagem sem tag fixa  
   - `image: fiware/orion-ld` puxa sempre `:latest`.  
   - Falta pinagem de versão (ex.: `fiware/orion-ld:2.4.0`) compromete reproducibilidade.

4. Ausência de securityContext  
   - Não há configuração de `runAsNonRoot`, `readOnlyRootFilesystem`, niquelas de capabilities.  
   - Sem isso, o container pode rodar como root e ter permissões desnecessárias.

5. Falta de política de afinidade/anti-afinidade  
   - Todos os Pods podem aglomerar num mesmo nó, sem spread.  
   - Recomenda-se usar `podAntiAffinity` para alta disponibilidade.

6. Não há PodDisruptionBudget (PDB)  
   - Sem PDB, upgrades/evictions podem derrubar todos os Pods simultaneamente.

7. HPA com minReplicas = replicas atuais  
   - `minReplicas: 3` igual a `spec.replicas: 3` impede scale-down.  
   - Se o objetivo for diminuir abaixo de 3, precisa ajustar o mínimo.

8. HPA depende de metrics-server  
   - Se não estiver instalado e configurado, o autoscaler não funcionará.

9. Recursos incompletos  
   - Foi declarado CPU e memória, mas não há request/limit para `ephemeral-storage`.  
   - Sem limitRange no namespace, o Pod pode monopolizar disco local.

10. Pod template metadata.name  
    - Definir `metadata.name` no template é redundante e potencialmente confuso (o nome do Pod será gerado pelo Deployment).

11. Caracteres não-ASCII em argumentos  
    - `usuariozão` no `-dbuser` pode causar problemas de encoding ou parsing em alguns shells/entrypoints.

12. Probes sem thresholds customizados  
    - Usa valores defaults de `failureThreshold` e `timeoutSeconds`.  
    - Em serviços críticos, vale definir timeouts e thresholds apropriados.

13. Ausência de `terminationGracePeriodSeconds`  
    - Poderá não dar tempo suficiente para shutdown ordernado, ou ficar com valores padrão não desejados.

14. Service type LoadBalancer  
    - Gera custo direto em cloud providers.  
    - Se for acessível via Ingress, talvez seja melhor usar ClusterIP + Ingress.

15. Não há validação de ingressos  
    - Sem NetworkPolicy, qualquer origem pode acessar o Service.  

Recomendações gerais:  
- Extrair credenciais para Secrets+ConfigMaps  
- Versionar imagens com tags imutáveis  
- Adicionar securityContext, affinity e PDB  
- Corrigir selector do Service  
- Validar necessidade de LoadBalancer vs Ingress/NodePort + NetworkPolicy

## Fix
✅ **Executado apply_manifest:**

```json
🚀 **Aplicado:** {'status': 'success', 'message': 'Sucesso:\ndeployment.apps/fiware-orionld configured\nservice/fiware-orionld-service configured\nhorizontalpodautoscaler.autoscaling/fiware-orionld-hpa unchanged\n'}
```

## K8s
```
NAME                              READY   STATUS              RESTARTS     AGE
fiware-orionld-548584cdf-4fvsp    0/1     Running             1 (7s ago)   32s
fiware-orionld-548584cdf-97bms    0/1     Running             1 (7s ago)   32s
fiware-orionld-548584cdf-xn8cp    0/1     Running             1 (7s ago)   32s
fiware-orionld-6d847b8bbb-jshld   0/1     ContainerCreating   0            1s
```