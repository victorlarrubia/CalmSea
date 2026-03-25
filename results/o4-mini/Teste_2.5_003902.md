# Teste 2-frontend.yaml - Rep 5

## Análise
Segue a lista de problemas e más-práticas de segurança identificadas neste Deployment:

1. Imagem mal especificada e sem tag fixa  
   - “image: nginxs” parece um typo (deveria ser “nginx”) e não aponta para uma tag ou digest versionado, fazendo com que o K8s puxe sempre “:latest”. Isso prejudica a rastreabilidade e pode receber builds não auditados.

2. Variável sensível hard-coded  
   - `PASSWORD_SERVICE_HOST: "123456"` está exposta no manifest. Qualquer pessoa com acesso ao Deployment verá o valor. Use um Secret K8s (ou CSI driver) para injetar credenciais de forma segura.

3. Ausência de recursos limits  
   - Só há `requests` de CPU/memória, sem `limits`. Um pod sem limites pode monopolizar recursos do nó (risco de DoS) e perder previsibilidade de escalonamento.

4. Falta de securityContext  
   - Por padrão o container roda como root e com todas as capabilities concedidas. Deve definir pelo menos:
     • runAsNonRoot: true  
     • allowPrivilegeEscalation: false  
     • readOnlyRootFilesystem: true  
     • dropCapabilities: ["ALL"]

5. Uso de ServiceAccount “default” sem restrições de RBAC  
   - Qualquer container que escale ou tenha vulnerabilidade poderá usar permissões excessivas. Crie um SA dedicado e atribua roles mínimos.

6. Sem probes de liveness/readiness  
   - Embora não seja diretamente “hackeável”, a falta de probes prejudica a resiliência da aplicação e torna o cluster menos estável, abrindo espaço para falhas persistentes.

7. Ausência de NetworkPolicy  
   - Todo tráfego intra-cluster está liberado por padrão, o que facilita movimento lateral caso algum pod seja comprometido.

8. imagePullPolicy implícita  
   - Para tags versionadas recomenda-se `imagePullPolicy: IfNotPresent` ou usar digests e `imagePullPolicy: Always` apenas em CI/CD controlado.

Recomendações gerais:  
• Use imagens com conteúdo escaneado e assinadas (OCI signing).  
• Separe config e segredos (ConfigMap vs Secret).  
• Aplique políticas de segurança (PSP/PSA, OPA/Gatekeeper).  
• Monitore uso de capabilities, privilégios e tráfego de rede.

## Fix
✅ **Executado apply_manifest:**

```json
🚀 **Aplicado:** {'status': 'success', 'message': 'Sucesso:\ndeployment.apps/frontend configured\n'}
```

## K8s
```
NAME                        READY   STATUS              RESTARTS   AGE
frontend-65d44dd469-jfx4q   0/1     ContainerCreating   0          0s
frontend-65d44dd469-kzn9s   0/1     ContainerCreating   0          0s
frontend-65d44dd469-wzhms   0/1     ImagePullBackOff    0          22s
frontend-f66456b77-85xmn    0/1     Pending             0          0s
```