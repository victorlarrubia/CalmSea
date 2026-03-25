# Teste 1-orion.yaml - Rep 2

## Análise
Erros e vulnerabilidades identificados no manifesto:

1. Hard-coded credentials  
   - O DB user/password aparecem diretamente em `args` (`-dbuser usuariozão -dbpwd 123456789`).  
   - As variáveis de ambiente `DB_PASSWORD` e `API_KEY` trazem segredos em texto plano.  
   Risco: vazamento em eventos, logs, dumps de pod, e fácil exfiltração por invasor.  
   Mitigação: movê-los para Kubernetes Secrets (via `envFrom: secretRef` ou mounted volume).

2. Ausência de securityContext  
   - Nenhum `securityContext` em nível de Pod ou Container.  
   - Não há `runAsNonRoot`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false` nem `capabilities.drop`.  
   Risco: container roda como root sem restrições, elevando ataque lateral ou breakout.  
   Mitigação: definir user não-root, montar FS somente leitura e dropar CAPs desnecessárias.

3. Exposição pública indiscriminada  
   - Service com `type: LoadBalancer` expõe porta 1027 diretamente à internet.  
   - Não há NetworkPolicy para limitar quais IPs/clientes podem acessar.  
   Risco: interface da API Orion-LD fica acessível sem controle de quem se conecta.  
   Mitigação: usar Ingress/API Gateway com autenticação, ou NetworkPolicy para restringir origens.

4. Service selector incorreto  
   - Service seleciona `app: orionlds`, mas o Deployment usa label `app: orionld`.  
   Consequência: o Service não irá encaminhar tráfego a nenhum pod. Provoca downtime ou troubleshooting.

5. Imagem sem tag e pullPolicy implícito  
   - `image: fiware/orion-ld` (sem versão fixa) pode puxar versões “latest” imprevistas.  
   - Falta declarar `imagePullPolicy`, levando a comportamento ambíguo.  
   Mitigação: usar tags específicas (ex: `:3.0.0`) e `imagePullPolicy: IfNotPresent` ou `Always`.

6. Falta de controle de armazenamento efêmero  
   - Não há requests/limits para `ephemeral-storage`.  
   Risco: pods podem consumir todo o disk do nó e comprometer demais workloads.  

7. Ausência de políticas de segurança do cluster  
   - Não há PodSecurityPolicy (ou PodSecurityAdmission) nem RBAC específico para limitar ações do pod.  
   Mitigação: aplicar Profiles de Pod Security (PSA) ou PSP/OPA/Gatekeeper para reforçar normas.

—  
Recomendação geral: revisar toda a configuração de segurança (ciência dos princípios de least privilege), externalizar segredos para Secrets, endurecer as políticas de rede e de runtime dos containers antes de subir em produção.

## Fix
✅ **Executado apply_manifest:**

```json
🚀 **Aplicado:** {'status': 'success', 'message': 'Sucesso:\nsecret/fiware-orionld-secret created\ndeployment.apps/fiware-orionld configured\nservice/fiware-orionld-service configured\nhorizontalpodautoscaler.autoscaling/fiware-orionld-hpa unchanged\n'}
```

## K8s
```
NAME                              READY   STATUS              RESTARTS      AGE
fiware-orionld-548584cdf-7jmcf    0/1     Running             1 (14s ago)   39s
fiware-orionld-548584cdf-s7cmb    0/1     Running             1 (14s ago)   39s
fiware-orionld-548584cdf-x9tqc    0/1     Running             1 (14s ago)   39s
fiware-orionld-558f4d5d49-d4f4k   0/1     ContainerCreating   0             0s
```