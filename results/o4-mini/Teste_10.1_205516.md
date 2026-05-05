# Relatório de Benchmark: 10-mongodb.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 1
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Aqui está o diagnóstico dos recursos atuais e a proposta de correção em ambiente de produção:

1) Service “mongodb-service”  
   Problema  
   - O selector é `app: nonexistent-mongodb`, mas o Deployment usa `app: mongodb-app`. Isso faz com que o Service não encontre nenhum Pod.  
   Correção  
   - Alinhar o selector do Service para `app: mongodb-app`.

2) Deployment “mongodb-deployment”  
   Problemas e sugestões de melhoria  
   a) Imagem sem tag fixa  
      - Atualmente `image: mongo`. Em produção sempre especificar versão (ex.: `mongo:6.0.8`).  
   b) Sem requests/limits de CPU e memória  
      - Adicionar `resources.requests` e `resources.limits` para evitar oversubscription.  
   c) Credenciais em texto claro no campo env  
      - Externalizar usuário e senha num Secret do Kubernetes e referenciar via `valueFrom`.  
   d) Volume efêmero (emptyDir)  
      - Em produção usar PersistentVolumeClaim para persistir dados do MongoDB.  
   e) Ausência de probes  
      - Incluir livenessProbe e readinessProbe para garantir saúde e disponibilidade.

3) Segurança e boas práticas  
   - ImagePullPolicy: alterar para `IfNotPresent` (ou `Always` apenas se fizer sentido ter sempre versão mais recente).  
   - Adicionar labels e annotations de versionamento se necessário.  
   - Definir `securityContext` mínimo (runAsNonRoot, fsGroup…)  

---  

A seguir o YAML corrigido e completo. Você pode primeiro testar com `kubectl apply --dry-run=client -f -` e depois aplicar:

```yaml
---
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
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mongo-pvc
  namespace: teste-mongodb
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: standard

---
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

---
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
        fsGroup: 999
      containers:
        - name: mongodb
          image: mongo:6.0.8
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 27017
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
          resources:
            requests:
              cpu: "100m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "1Gi"
          volumeMounts:
            - name: mongo-storage
              mountPath: /data/db
          readinessProbe:
            exec:
              command:
                - mongo
                - --eval
                - "db.adminCommand('ping')"
            initialDelaySeconds: 15
            periodSeconds: 10
            timeoutSeconds: 5
          livenessProbe:
            exec:
              command:
                - mongo
                - --eval
                - "db.adminCommand('ping')"
            initialDelaySeconds: 30
            periodSeconds: 20
            timeoutSeconds: 5
      volumes:
        - name: mongo-storage
          persistentVolumeClaim:
            claimName: mongo-pvc
```

Para aplicar:

kubectl apply --dry-run=client -f corrected-mongodb.yaml  
kubectl apply -f corrected-mongodb.yaml  

Com isso:  
- Service passa a selecionar corretamente os Pods.  
- O MongoDB roda com storage persistente, probes e limites de recursos.  
- Credenciais ficam seguras no Secret.  
- Imagem está com tag fixa.

## 📋 Estado Final do Namespace (teste-mongodb)
```
NAME                                      READY   STATUS    RESTARTS   AGE
pod/mongodb-deployment-559d9986d4-f6g58   1/1     Running   0          3m15s
pod/mongodb-deployment-6c8fd9688b-lgfd8   0/1     Pending   0          2m17s

NAME                      TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)     AGE
service/mongodb-service   ClusterIP   10.107.108.48   <none>        27017/TCP   3m15s

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/mongodb-deployment   1/1     1            1           3m15s

NAME                                            DESIRED   CURRENT   READY   AGE
replicaset.apps/mongodb-deployment-559d9986d4   1         1         1       3m15s
replicaset.apps/mongodb-deployment-6c8fd9688b   1         1         0       2m18s
replicaset.apps/mongodb-deployment-79969fc84f   0         0         0       2m43s
```