# Relatório de Benchmark: 10-mongodb.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 2
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
A seguir o diagnóstico dos recursos atuais e as recomendações com os YAMLs alinhados a boas-práticas de produção.

1) Service “mongodb-service”  
   - Problema: selector app: nonexistent-mongodb não casa com as labels dos pods (“app: mongodb-app”), logo não há endpoint.  
   - Correção: alinhar selector com label do Deployment.

2) Deployment “mongodb-deployment”  
   - Usa emptyDir para /data/db (ephemeral). Em produção precisa PVC para persistência.  
   - Não há resourceRequests/limits ⇒ risco de “noisy neighbor”.  
   - Imagem “mongo” sem tag fixa ⇒ difícil controlar upgrades.  
   - Credenciais em cleartext em env ⇒ use Secret.  
   - Sem readiness/liveness probes ⇒ demora a detectar falhas.  
   - Roda como root (securityContext vazio).  
   - imagePullPolicy Always em imagem versionada ⇒ desnecessário.

3) PVC  
   - Em caso de existir um PVC antigo com spec diferente, lembre-se: spec é imutável após bind. Se precisar alterá-lo, deve recriar (com cuidado) ou criar um novo.

4) Secret  
   - Criação de Secret para credenciais.

―――  
Abaixo o conjunto de manifestos corrigidos. Ajuste o número de réplicas e storage conforme necessidade.

```yaml
# 1. Secret com credenciais
apiVersion: v1
kind: Secret
metadata:
  name: mongodb-secret
  namespace: teste-mongodb
type: Opaque
stringData:
  MONGO_INITDB_ROOT_USERNAME: admin
  MONGO_INITDB_ROOT_PASSWORD: SecurePassword123!

---
# 2. PVC para persistência
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mongodb-pvc
  namespace: teste-mongodb
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard

---
# 3. Service corrigido
apiVersion: v1
kind: Service
metadata:
  name: mongodb-service
  namespace: teste-mongodb
  labels:
    app: mongodb-app
spec:
  type: ClusterIP
  selector:
    app: mongodb-app
  ports:
    - name: mongodb
      port: 27017
      targetPort: 27017
      protocol: TCP

---
# 4. Deployment otimizado
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mongodb-deployment
  namespace: teste-mongodb
  labels:
    app: mongodb-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mongodb-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: mongodb-app
    spec:
      securityContext:
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      containers:
        - name: mongodb-container
          image: mongo:6.0.5
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 27017
              protocol: TCP
          env:
            - name: MONGO_INITDB_ROOT_USERNAME
              valueFrom:
                secretKeyRef:
                  name: mongodb-secret
                  key: MONGO_INITDB_ROOT_USERNAME
            - name: MONGO_INITDB_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mongodb-secret
                  key: MONGO_INITDB_ROOT_PASSWORD
          args:
            - "--auth"
          readinessProbe:
            tcpSocket:
              port: 27017
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 5
          livenessProbe:
            tcpSocket:
              port: 27017
            initialDelaySeconds: 15
            periodSeconds: 20
            timeoutSeconds: 5
          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"
          volumeMounts:
            - name: mongo-storage
              mountPath: /data/db
      volumes:
        - name: mongo-storage
          persistentVolumeClaim:
            claimName: mongodb-pvc
```

Para aplicar:

1. (Se existir PVC antigo com nome igual e spec diferente, avalie recriá-lo ou criar um novo com nome distinto.)  
2. kubectl apply -f mongodb-secret.yaml    -n teste-mongodb  
3. kubectl apply -f mongodb-pvc.yaml       -n teste-mongodb  
4. kubectl apply -f mongodb-service.yaml   -n teste-mongodb  
5. kubectl apply -f mongodb-deployment.yaml -n teste-mongodb  

Se houver conflito em Service ou Deployment:  
   kubectl delete svc/mongodb-service deployment.apps/mongodb-deployment -n teste-mongodb  
   reaplique os manifests.  

Dessa forma você terá:  
- tráfego corretamente routed (“selector” alinhado),  
- dados persistidos em PVC,  
- credenciais seguras em Secret,  
- limites de recursos e probes configurados,  
- imagem com tag fixa e política de pull adequada,  
- segurança de usuário não-root.

## 📋 Estado Final do Namespace (teste-mongodb)
```
NAME                                      READY   STATUS    RESTARTS   AGE
pod/mongodb-deployment-56d9b6b5d8-q4mjh   0/1     Pending   0          3m1s
pod/mongodb-deployment-7d5cb554cc-bc65z   0/1     Pending   0          2m26s
pod/mongodb-deployment-8cf749fb7-842qq    0/1     Pending   0          3m1s
pod/mongodb-deployment-8cf749fb7-9c4bg    0/1     Pending   0          3m30s

NAME                      TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)     AGE
service/mongodb-service   ClusterIP   10.100.212.114   <none>        27017/TCP   4m27s

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/mongodb-deployment   0/3     1            0           4m27s

NAME                                            DESIRED   CURRENT   READY   AGE
replicaset.apps/mongodb-deployment-559d9986d4   0         0         0       4m27s
replicaset.apps/mongodb-deployment-56d9b6b5d8   1         1         0       3m1s
replicaset.apps/mongodb-deployment-7d5cb554cc   1         1         0       2m27s
replicaset.apps/mongodb-deployment-8cf749fb7    2         2         0       3m30s
```