# Relatório: 2-frontend.yaml - Rep 1

## Status Final: ✅ SUCESSO
**Veredito:** Sucesso: Ambiente íntegro e estável

---

## 🔍 Análise
O deployment "frontend" foi deletado com sucesso e, em seguida, foi recriado no namespace "teste-frontend". 

Aqui está a versão corrigida do YAML que foi aplicada:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: teste-frontend
spec:
  progressDeadlineSeconds: 600
  replicas: 1
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      app: guestbook
      tier: frontend
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    type: RollingUpdate
  template:
    metadata:
      labels:
        app: guestbook
        tier: frontend
    spec:
      containers:
      - env:
        - name: GET_HOSTS_FROM
          value: dns
        - name: PASSWORD_SERVICE_HOST
          value: "123456"
        image: nginxs
        imagePullPolicy: Always
        name: php-redis
        ports:
        - containerPort: 80
          protocol: TCP
        resources:
          requests:
            cpu: 100m
            memory: 100Mi
        terminationMessagePath: /dev/termination-log
        terminationMessagePolicy: File
      dnsPolicy: ClusterFirst
      restartPolicy: Always
      schedulerName: default-scheduler
      securityContext: {}
      terminationGracePeriodSeconds: 30
```

Se precisar de mais alguma coisa, estou à disposição!

## 🛠️ Fix Aplicado
```yaml
O deployment "frontend" foi deletado com sucesso e, em seguida, foi recriado no namespace "teste-frontend". 

Aqui está a versão corrigida do YAML que foi aplicada:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: teste-frontend
spec:
  progressDeadlineSeconds: 600
  replicas: 1
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      app: guestbook
      tier: frontend
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    type: RollingUpdate
  template:
    metadata:
      labels:
        app: guestbook
        tier: frontend
    spec:
      containers:
      - env:
        - name: GET_HOSTS_FROM
          value: dns
        - name: PASSWORD_SERVICE_HOST
          value: "123456"
        image: nginxs
        imagePullPolicy: Always
        name: php-redis
        ports:
        - containerPort: 80
          protocol: TCP
        resources:
          requests:
            cpu: 100m
            memory: 100Mi
        terminationMessagePath: /dev/termination-log
        terminationMessagePolicy: File
      dnsPolicy: ClusterFirst
      restartPolicy: Always
      schedulerName: default-scheduler
      securityContext: {}
      terminationGracePeriodSeconds: 30
```

Se precisar de mais alguma coisa, estou à disposição!
```

## 📋 Cluster Snapshot
```
NAME                           READY   STATUS    RESTARTS   AGE
pod/frontend-f689c955b-6vr7n   1/1     Running   0          9s

NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/frontend   1/1     1            1           9s

NAME                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/frontend-f689c955b   1         1         1       9s
```