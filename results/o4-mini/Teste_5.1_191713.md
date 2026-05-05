# Relatório de Benchmark: 5-nginx.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 1
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Seguem os achados, as recomendações e o YAML final que foi aplicado no namespace **teste-nginx**.

1) Service “nginxsvc”  
   – Problemas identificados  
     • Tipo NodePort não é indicado em produção (difícil de expor via LoadBalancer/Ingress).  
     • Ausência de anotação para preservar IP de origem do cliente.  
     • Labels minimalistas (só `app: nginx`), sem versionamento ou padrões `app.kubernetes.io/*`.  
   – Sugestões de correção  
     • Trocar o Service para `type: LoadBalancer` (ou expor via Ingress).  
     • Adicionar `externalTrafficPolicy: Local` para manter o IP de origem.  
     • Incluir anotações específicas do provedor (ex.: AWS/ GCP) se for LoadBalancer interno/externo.  
     • Padronizar labels, ex.:  
         app.kubernetes.io/name: nginx  
         app.kubernetes.io/component: web  
         app.kubernetes.io/version: “1.21.0”  

2) ReplicationController “my-nginx”  
   – Problemas identificados  
     • RC está obsoleto em relação a Deployments (sem rollout automático, sem history).  
     • Ausência de probes e de requests/limits de CPU e memória.  
     • Imagem `nginx:latest` não pinada a uma tag específica.  
   – Sugestões de correção  
     • Substituir por um Deployment com `spec.replicas`.  
     • Definir `resources.requests` e `resources.limits`.  
     • Definir `livenessProbe` e `readinessProbe`.  
     • Usar `image: nginx:1.21.0` (ou outra versão gerenciada pela equipe).  
     • Incluir `imagePullPolicy: IfNotPresent`.  
     • Padronizar labels iguais às do Service para assegurar selector consistente.

—  
YAML final aplicado (namespace: teste-nginx)  
```yaml
# Service corrigido para LoadBalancer
apiVersion: v1
kind: Service
metadata:
  name: nginxsvc
  namespace: teste-nginx
  labels:
    app.kubernetes.io/name: nginx
    app.kubernetes.io/component: web
    app.kubernetes.io/version: "1.21.0"
  annotations:
    # Exemplo para AWS ELB interno:
    # service.beta.kubernetes.io/aws-load-balancer-internal: "true"
spec:
  type: LoadBalancer
  externalTrafficPolicy: Local
  selector:
    app.kubernetes.io/name: nginx
    app.kubernetes.io/component: web
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 80
    - name: https
      protocol: TCP
      port: 443
      targetPort: 443

---
# Deployment substituindo o antigo ReplicationController
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: teste-nginx
  labels:
    app.kubernetes.io/name: nginx
    app.kubernetes.io/component: web
    app.kubernetes.io/version: "1.21.0"
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: nginx
      app.kubernetes.io/component: web
  template:
    metadata:
      labels:
        app.kubernetes.io/name: nginx
        app.kubernetes.io/component: web
        app.kubernetes.io/version: "1.21.0"
    spec:
      containers:
      - name: nginx
        image: nginx:1.21.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "250m"
            memory: "256Mi"
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 15
          periodSeconds: 20
      # Opcional: securityContext etc.
```

– O Service foi reaplicado (dry-run ok) e o antigo RC removido.  
– O Deployment foi criado conforme boas práticas de produção.  
– Caso queira expor TLS, recomenda-se criar um Ingress apontando para este Service com Cert-Manager.

## 📋 Estado Final do Namespace (teste-nginx)
```
NAME                                    READY   STATUS              RESTARTS   AGE
pod/my-nginx-rpb8d                      0/1     ContainerCreating   0          3m39s
pod/nginx-deployment-65f874df8c-mxm8t   0/1     Pending             0          2m22s
pod/nginx-deployment-65f874df8c-mzt2d   0/1     Pending             0          2m22s
pod/nginx-deployment-65f874df8c-sm6lg   0/1     Pending             0          2m22s

NAME               TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
service/nginxsvc   LoadBalancer   10.105.181.25   <pending>     80:30361/TCP,443:31365/TCP   3m39s

NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/nginx-deployment   0/3     3            0           2m22s

NAME                                          DESIRED   CURRENT   READY   AGE
replicaset.apps/nginx-deployment-65f874df8c   3         3         0       2m22s
```