# Relatório: 9-storm.yaml - Rep 1

## Status Final: ✅ SUCESSO
**Veredito:** Sucesso: Ambiente íntegro e estável

---

## 🔍 Análise
O deployment `storm-worker-controller` foi deletado com sucesso e, em seguida, foi recriado no namespace `teste-storm`. 

Aqui está a versão corrigida do YAML que foi aplicada:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  annotations: {}
  labels:
    name: storm-worker
  name: storm-worker-controller
  namespace: teste-storm
spec:
  progressDeadlineSeconds: 600
  replicas: 1
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      name: storm-worker
      uses: nimbus
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    type: RollingUpdate
  template:
    metadata:
      labels:
        name: storm-worker
        uses: nimbus
    spec:
      containers:
      - args:
        - echo 'Worker stub iniciado...'; while true; do sleep 3600; done
        command:
        - /bin/sh
        - -c
        env:
        - name: STORM_NIMBUS_PASSWORD
          value: storm-admin-123
        - name: STORM_NIMBUS
          value: nimbus.default.svc.cluster.local
        - name: STORM_ZOOKEEPER_SERVERS
          value: zookeeper.default.svc.cluster.local:2181
        image: storm
        imagePullPolicy: Always
        name: storm-worker
        ports:
        - containerPort: 6700
          protocol: TCP
        - containerPort: 6701
          protocol: TCP
        - containerPort: 6702
          protocol: TCP
        - containerPort: 6703
          protocol: TCP
        resources:
          limits:
            cpu: 30m
            memory: 20Mi
          requests:
            cpu: 30m
            memory: 10Mi
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
O deployment `storm-worker-controller` foi deletado com sucesso e, em seguida, foi recriado no namespace `teste-storm`. 

Aqui está a versão corrigida do YAML que foi aplicada:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  annotations: {}
  labels:
    name: storm-worker
  name: storm-worker-controller
  namespace: teste-storm
spec:
  progressDeadlineSeconds: 600
  replicas: 1
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      name: storm-worker
      uses: nimbus
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    type: RollingUpdate
  template:
    metadata:
      labels:
        name: storm-worker
        uses: nimbus
    spec:
      containers:
      - args:
        - echo 'Worker stub iniciado...'; while true; do sleep 3600; done
        command:
        - /bin/sh
        - -c
        env:
        - name: STORM_NIMBUS_PASSWORD
          value: storm-admin-123
        - name: STORM_NIMBUS
          value: nimbus.default.svc.cluster.local
        - name: STORM_ZOOKEEPER_SERVERS
          value: zookeeper.default.svc.cluster.local:2181
        image: storm
        imagePullPolicy: Always
        name: storm-worker
        ports:
        - containerPort: 6700
          protocol: TCP
        - containerPort: 6701
          protocol: TCP
        - containerPort: 6702
          protocol: TCP
        - containerPort: 6703
          protocol: TCP
        resources:
          limits:
            cpu: 30m
            memory: 20Mi
          requests:
            cpu: 30m
            memory: 10Mi
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
NAME                                           READY   STATUS    RESTARTS   AGE
pod/storm-worker-controller-654c85d79d-rhgkb   1/1     Running   0          22s

NAME                                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/storm-worker-controller   1/1     1            1           22s

NAME                                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/storm-worker-controller-654c85d79d   1         1         1       22s
```