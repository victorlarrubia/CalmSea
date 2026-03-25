# Teste 1-orion.yaml - Rep 3

## Análise
Segue a análise dos problemas e vulnerabilidades encontrados nesse manifesto:

1.  Hard-coded credentials  
    • DB_PASSWORD e API_KEY definidos diretamente em env vars.  
    • Usuário/senha do Mongo também trafegam em args (“-dbuser… -dbpwd…”).  
    Risco: exposição fácil de segredos (logs, `kubectl describe pod`, status do container). Deve-se usar objeto Secret e montar via ambiente ou volume.

2.  Service Account sem restrições (default)  
    • Não há RBAC nem ServiceAccount customizado.  
    Risco: se um container for comprometido, usará permissões amplas do cluster. Recomenda-se criar ServiceAccount com Role/RoleBinding mínimos.

3.  Ausência de securityContext  
    • Nenhum `runAsNonRoot`, `runAsUser`, `fsGroup`, `readOnlyRootFilesystem`, nem drop de capabilities.  
    Risco: container pode rodar como root e ter permissões excessivas. Deve-se aplicar contexto que restrinja privilégios.

4.  Imagem sem tag fixa e sem imagePullPolicy explícito  
    • `image: fiware/orion-ld` equivale a `:latest`.  
    • Sem `imagePullPolicy`, o padrão é `Always` para latest – difícil reproduzir deploy e propenso a “drift”.  
    Recomenda-se usar tags versões imutáveis e `imagePullPolicy: IfNotPresent` ou `Always` conforme o ciclo.

5.  Service sem roteamento (label mismatch)  
    • Service seleciona `app: orionlds` mas Deployment usa `app: orionld`.  
    • Resultado: não há endpoints associados – tráfego nunca chega nos pods.

6.  Falta de NetworkPolicy  
    • Não há restrição de tráfego entre pods/Namespaces.  
    Risco: lateral movement caso algum serviço seja comprometido. Criar políticas que limitem conexões somente ao que for estritamente necessário.

7.  Ausência de PodDisruptionBudget (PDB)  
    • Sem PDB, upgrades/evictions (drain) podem derrubar mais réplicas que o desejado, reduzindo disponibilidade. Defina PDB com `minAvailable` ou `maxUnavailable`.

8.  Falta de estratégia de atualização explícita  
    • Não há `spec.strategy` no Deployment.  
    • O padrão (`RollingUpdate`) é aplicado, mas sem parâmetros pode causar indisponibilidade ou longo período de pods “não prontos”. Recomenda-se definir `maxSurge` e `maxUnavailable`.

9.  Probes sem TLS e sem timeouts/customizações  
    • Liveness e readiness usam HTTP sem autenticação nem TLS.  
    • Sem `timeoutSeconds` ou `failureThreshold` ajustados, pode haver reboot desnecessário ou false-positives em rede lenta.

10. HPA usando métricas de memória  
    • Métrica de memória só funciona se houver Metrics Server ou adapter instalado e configurado corretamente.  
    • Falha na coleta causa HPA inoperante. Confirme a presença de Metrics Server e testez as métricas.

Resumo: o manifesto expõe segredos em claro, não segue boas práticas de privilégio mínimo nem de governança de tráfego, e contém um erro de label no Service que impede o roteamento. Recomenda-se corrigir cada ponto aplicando Secrets, contextos de segurança, políticas de rede, RBAC restrito, PDB/strategy e consertar o seletor do Service.

## Fix
✅ **Executado apply_manifest:**

```json
🚀 **Aplicado:** {'status': 'success', 'message': 'Sucesso:\nsecret/orionld-secrets configured\ndeployment.apps/fiware-orionld configured\nservice/fiware-orionld-service configured\nhorizontalpodautoscaler.autoscaling/fiware-orionld-hpa unchanged\n'}
```

## K8s
```
NAME                              READY   STATUS              RESTARTS   AGE
fiware-orionld-548584cdf-6q6mg    0/1     Running             0          26s
fiware-orionld-548584cdf-jn7jh    0/1     Running             0          26s
fiware-orionld-548584cdf-xgwmv    0/1     Running             0          26s
fiware-orionld-679fdbd5f6-7dlw5   0/1     ContainerCreating   0          1s
```