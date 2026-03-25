# Teste 1-orion.yaml - Rep 1

## Análise
Segue a auditoria de segurança e configuração no YAML enviado. Abaixo os principais problemas e más práticas identificadas:

1. Segredos embutidos em variáveis de ambiente  
   - As variáveis `DB_PASSWORD` e `API_KEY` estão com valores hard-coded no Deployment.  
   - O usuário e senha do MongoDB (`-dbuser "usuariozão"`, `-dbpwd "123456789"`) também vazam nos argumentos do container.  
   – Recomendação: mover tudo para um Secret e referenciar via `envFrom`/`valueFrom`.

2. Imagem sem tag fixa  
   - `image: fiware/orion-ld` puxa sempre a última versão (não determinística).  
   – Recomendação: fixar uma tag ou digest (`fiware/orion-ld:1.4.0` ou `@sha256:…`).

3. Ausência de imagePullPolicy  
   - Sem `imagePullPolicy` explícito, o padrão pode não ser o desejado em produção.  
   – Recomendação: definir `imagePullPolicy: IfNotPresent` ou `Always`, conforme estratégia de deploy.

4. Falta de SecurityContext  
   - Não há `securityContext` nem no Pod nem no Container.  
   – Riscos: os containers rodam como root, não há isolamento de usuário, não há drop de capabilities nem filesystem read-only.  
   – Recomendação:  
     • `runAsNonRoot: true`, `runAsUser: <UID>`, `readOnlyRootFilesystem: true`  
     • Dropar todas as capacidades extras (`capabilities.drop: ["ALL"]`).

5. Serviço sem correspondência de selector  
   - O Service seleciona `app: orionlds` enquanto o Deployment rotula os pods como `app: orionld` (sem “s”).  
   – Resultado: nenhum pod atenderá ao Service.

6. Service tipo LoadBalancer sem restrição  
   - Expõe a aplicação diretamente na Internet sem firewall ou whitelist de IP.  
   – Recomendação: usar Ingress com WAF/NACL ou adicionar Security Group / NetworkPolicy.

7. Ausência de NetworkPolicy  
   - Por padrão, qualquer pod pode se comunicar com este Deployment.  
   – Risco: lateral movement em caso de invasão de outro pod.  
   – Recomendação: criar NetworkPolicy para restringir acesso apenas ao que for necessário.

8. Probes com configuração mínima  
   - `livenessProbe`/`readinessProbe` sem `failureThreshold` ou `timeoutSeconds` customizados.  
   – Risco: detecções prematuras de falha ou timeouts muito curtinhos.  
   – Recomendação: ajustar `failureThreshold`, `timeoutSeconds` e `successThreshold` conforme comportamento real.

9. HPA sem efetivo escalonamento descendente  
   - `minReplicas: 3` igual ao `spec.replicas` original (3) faz o Deployment nunca descer abaixo de 3.  
   – Não é necessariamente errado, mas pode gerar custo extra se a carga for baixa.

10. Dependência de metrics-server  
   - HPA v2 com métricas de CPU e memória exige metrics-server rodando e configurado.  
   – Sem ele, o HPA ficará inativo (eventualmente escalando até o `maxReplicas` sem dados reais).

Resumo: mover segredos para Kubernetes Secret, corrigir selector do Service, fixar tags de imagem, endurecer securityContext e isolar rede via NetworkPolicy/In­gress.

## Fix
✅ **Executado apply_manifest:**

```json
🚀 **Aplicado:** {'status': 'success', 'message': 'Sucesso:\nsecret/fiware-orionld-secret configured\ndeployment.apps/fiware-orionld configured\nservice/fiware-orionld-service configured\nhorizontalpodautoscaler.autoscaling/fiware-orionld-hpa unchanged\n'}
```

## K8s
```
NAME                              READY   STATUS              RESTARTS      AGE
fiware-orionld-548584cdf-fzg8k    0/1     Running             1 (17s ago)   43s
fiware-orionld-548584cdf-jgcmn    0/1     Running             1 (17s ago)   43s
fiware-orionld-548584cdf-rjssk    0/1     Running             1 (17s ago)   43s
fiware-orionld-54ddccd7f7-mb5mg   0/1     ContainerCreating   0             0s
```