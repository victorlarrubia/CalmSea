# Relatório de Benchmark: 5-nginx.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 2
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Segue análise dos recursos e propostas de correção, seguidas dos manifests ajustados.

1) Service “nginxsvc”
   Problemas detectados:
   - Tipo NodePort não é o mais indicado em produção (geralmente usa-se LoadBalancer ou Ingress).
   - Falta de annotations para health-check / timeouts.
   - Não há definição de externalTrafficPolicy se for LB.
   - Ausência de labels de versão (úteis para monitoramento).
   Correções sugeridas:
   - Trocar type: NodePort por LoadBalancer (ou deixar ClusterIP e expor via Ingress).
   - Adicionar labels “app” e “version”.
   - Incluir annotation de health-check (se LB em cloud).
   - Remover porta 443 se não houver TLS no Service (delegar TLS ao Ingress/Proxy).

2) Deployment “my-nginx”
   (substituindo o RC para utilizar recursos de rolling updates)
   Problemas detectados:
   - Não há Deployment, apenas RC; RC não suporta strategy de atualização.
   - Falta de resource requests/limits.
   - Sem probes de readiness/liveness.
   - Imagem sem tag fixa (ex: “nginx:latest”).
   - Sem labels de version.
   - Ausência de securityContext (rodar como root).
   Correções sugeridas:
   - Criar um Deployment com strategy RollingUpdate.
   - Definir replicas ≥3 para alta disponibilidade.
   - Incluir requests/limits de CPU/memória.
   - Configurar readinessProbe e livenessProbe.
   - Fixar imagem, ex: nginx:1.24.0-alpine.
   - Rodar contêiner com usuário não-root.
   - Acrescentar labels “app” e “version”.

---

Manifests corrigidos:

```yaml
# Service corrigido (type=LoadBalancer)
apiVersion: v1
kind: Service
metadata:
  name: nginxsvc
  namespace: teste-nginx
  labels:
    app: nginx
    version: "1.24.0"
  annotations:
    # Ajuste conforme provedor de LB (ex. AWS, GCP)
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-port: "80"
    service.beta.kubernetes.io/aws-load-balancer-connection-idle-timeout: "3600"
spec:
  type: LoadBalancer
  selector:
    app: nginx
    version: "1.24.0"
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 80
```

```yaml
# Deployment corrigido
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-nginx
  namespace: teste-nginx
  labels:
    app: nginx
    version: "1.24.0"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
      version: "1.24.0"
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  template:
    metadata:
      labels:
        app: nginx
        version: "1.24.0"
    spec:
      securityContext:
        runAsUser: 1000
        runAsNonRoot: true
      containers:
      - name: nginx
        image: nginx:1.24.0-alpine
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
      # (opcional) nodeSelector, tolerations, affinity para alta disponibilidade
```

Próximos passos:
1. Validar com `kubectl apply --dry-run=client -f <arquivo>`.
2. Caso não haja conflitos, aplicar com `kubectl apply -f`.
3. Se persistir conflito (ex.: RC existindo), deletar RC antigo antes de aplicar.
4. Monitorar rollout: `kubectl rollout status deployment/my-nginx -n teste-nginx`.

## 📋 Estado Final do Namespace (teste-nginx)
```
NAME                           READY   STATUS              RESTARTS   AGE
pod/my-nginx-65f8c6c4d-2rvzk   0/1     Pending             0          2m19s
pod/my-nginx-65f8c6c4d-2w5tr   0/1     Pending             0          2m19s
pod/my-nginx-65f8c6c4d-4646x   0/1     Pending             0          2m19s
pod/my-nginx-chw8t             0/1     ContainerCreating   0          3m34s

NAME                             DESIRED   CURRENT   READY   AGE
replicationcontroller/my-nginx   1         1         0       3m34s

NAME               TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
service/nginxsvc   LoadBalancer   10.100.36.198   <pending>     80:32666/TCP,443:31921/TCP   2m19s

NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/my-nginx   0/3     3            0           2m19s

NAME                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/my-nginx-65f8c6c4d   3         3         0       2m19s
```