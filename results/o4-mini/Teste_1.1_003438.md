# Teste 1-orion.yaml - Rep 1

## Análise
Segue a análise de segurança e de configuração desse manifesto YAML, com os principais problemas identificados:

1. Hard-coded de credenciais  
   - As variáveis de ambiente `DB_PASSWORD` e `API_KEY` contêm segredos em texto claro.  
   - Além disso, no campo `args` são passados `-dbuser usuariozão` e `-dbpwd 123456789`, o que expõe ainda mais as credenciais.  
   – Recomendação: usar objetos do tipo Secret e referenciá-los via `envFrom` ou `env.secretKeyRef`.

2. Falta de securityContext  
   - O contêiner roda com usuário root por padrão.  
   - Não há restrições de privilégios (capabilities, readOnlyRootFilesystem, runAsNonRoot etc.).  
   – Recomendação: definir `securityContext` no Pod/Container para rodar como usuário não-root, limitar capabilities e tornar o sistema de arquivos somente leitura.

3. Imagem sem tag explícita  
   - `image: fiware/orion-ld` usa a tag “latest” implícita.  
   – Risco: variações de versão inesperadas em cada deploy.  
   – Recomendação: sempre especificar uma tag imutável (ex: `fiware/orion-ld:2.5.0`).

4. Falta de política de pull de imagem  
   - Não foi definido `imagePullPolicy` (padrão IfNotPresent), o que pode mascarar atualizações de imagem.  
   – Recomendação: para “latest” usar `Always` ou para tags fixas usar `IfNotPresent`.

5. Service selector incorreto  
   - O Service seleciona pods com `app: orionlds`, mas o Deployment rotula como `app: orionld`.  
   – Consequência: o Service não vai enxergar nenhum Pod, impactando disponibilidade.

6. Exposição desprotegida  
   - Service do tipo `LoadBalancer` expõe diretamente a aplicação sem controle de acesso.  
   – Recomendação: aplicar NetworkPolicy, Ingress com WAF ou firewall para restringir origem de tráfego.

7. Ausência de NetworkPolicy  
   - Não há nenhuma restrição de tráfego de/nos Pods, ampliando a superfície de ataque interno.

8. Sem estratégias de afinidade/anti-afinidade  
   - Todos os réplicas podem acabar no mesmo nó, criando ponto único de falha físico.  
   – Recomendação: adicionar `podAntiAffinity` para espalhar réplicas por nós diferentes.

9. Probes sem TLS  
   - `livenessProbe` e `readinessProbe` usam HTTP não criptografado.  
   – Recomendação: se a aplicação suportar HTTPS, usar probes TLS ou mTLS interno.

10. HPA com thresholds muito baixos  
   - CPU de 30% pode causar escala desnecessária em picos transitórios.  
   – Recomendação: ajustar thresholds conforme perfil de carga real.

Corrigindo esses pontos você terá um manifesto mais seguro e resiliente em produção.

## Fix
✅ **Executado apply_manifest:**

```json
🚀 **Aplicado:** {'status': 'success', 'message': 'Sucesso:\nsecret/fiware-orionld-secrets created\ndeployment.apps/fiware-orionld configured\nservice/fiware-orionld-service configured\nhorizontalpodautoscaler.autoscaling/fiware-orionld-hpa unchanged\n'}
```

## K8s
```
NAME                             READY   STATUS              RESTARTS      AGE
fiware-orionld-548584cdf-f56m6   0/1     Running             1 (15s ago)   40s
fiware-orionld-548584cdf-rt5wl   0/1     Running             1 (15s ago)   40s
fiware-orionld-548584cdf-sp9nk   0/1     Running             1 (15s ago)   40s
fiware-orionld-8d5c8dff7-t6v69   0/1     ContainerCreating   0             0s
```