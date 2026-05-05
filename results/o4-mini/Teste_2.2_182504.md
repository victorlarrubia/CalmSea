# Relatório de Benchmark: 2-frontend.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 2
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod frontend-65d44dd469-c48ml: ImagePullBackOff

## 🧠 Raciocínio do Agente
A seguir o diagnóstico dos recursos atuais e as correções recomendadas, seguido do YAML final aplicado.

1) Problemas identificados no Deployment “frontend”  
   • Imagem incorreta/typo: `nginxs` (não existe).  
   • Versão de imagem não pinada (usar tag sem “latest”).  
   • Nome do container (“php-redis”) não bate com a imagem (nginx).  
   • Variável de ambiente `GET_HOSTS_FROM` é obsoleta.  
   • Variável `PASSWORD_SERVICE_HOST` exposta em clear-text (deve ser Secret).  
   • Faltam liveness e readiness probes.  
   • Só há requests, não há resource limits.  
   • Ausência de labels padrão (“app.kubernetes.io/*”).  
   • securityContext vazio (não força runAsNonRoot, readOnlyRootFilesystem etc.).

2) Ausência de Service  
   • Não havia Service “frontend” no namespace; sem ele, não há acesso interno/externo.

--------------------------------------------------------------------------------
Correções aplicadas no YAML (namespace: teste-frontend):

apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: teste-frontend
  labels:
    app.kubernetes.io/name: frontend
    app.kubernetes.io/part-of: guestbook
    app.kubernetes.io/component: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: frontend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
  template:
    metadata:
      labels:
        app.kubernetes.io/name: frontend
        app.kubernetes.io/part-of: guestbook
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: nginx
        image: nginx:1.21.6-alpine
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 80
          protocol: TCP
        env:
        - name: PASSWORD_SERVICE_HOST
          valueFrom:
            secretKeyRef:
              name: guestbook-secrets
              key: password_service_host
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 250m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
        volumeMounts:
        - name: tmp
          mountPath: /tmp
          readOnly: false
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
      volumes:
      - name: tmp
        emptyDir: {}

---

apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: teste-frontend
  labels:
    app.kubernetes.io/name: frontend
    app.kubernetes.io/part-of: guestbook
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: frontend
  ports:
  - name: http
    port: 80
    targetPort: http

--------------------------------------------------------------------------------
Próximos passos  
• Garanta que o Secret `guestbook-secrets` exista com a chave `password_service_host`.  
• Monitore pods para verificar probes e consumo de recursos.  
• Ajuste réplicas e liveness/readiness conforme carga real.  
• Considere Ingress/LoadBalancer se expor externamente.

## 📋 Estado Final do Namespace (teste-frontend)
```
NAME                            READY   STATUS             RESTARTS   AGE
pod/frontend-5cfd9c99b9-z7hd8   0/1     Pending            0          12s
pod/frontend-65d44dd469-62k7n   0/1     Pending            0          12s
pod/frontend-65d44dd469-c48ml   0/1     ImagePullBackOff   0          57s
pod/frontend-65d44dd469-whkz5   0/1     Pending            0          12s

NAME               TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/frontend   LoadBalancer   10.102.91.34   <pending>     80:32049/TCP   12s

NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/frontend   0/3     1            0           58s

NAME                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/frontend-5cfd9c99b9   1         1         0       13s
replicaset.apps/frontend-65d44dd469   3         3         0       58s
```