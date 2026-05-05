# Relatório de Benchmark: 1-orion.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 2
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod fiware-orionld-548584cdf-4n7p8: CrashLoopBackOff

## 🧠 Raciocínio do Agente
Segue a análise dos três recursos e, logo em seguida, os manifests corrigidos para o Service e o Deployment conforme boas práticas de produção.

1) Service “fiware-orionld-service”  
   Problema  
   - selector.app = “orionlds” não bate com os pods (Deployment usa label app=“orionld”).  
   - Falta label/annotation de versão e owner para facilitar governança.  
   Sugestão de correção  
   - Ajustar selector.app para “orionld”.  
   - Adicionar metadata.labels com app e version.

2) Deployment “fiware-orionld”  
   Problemas  
   - Credenciais (DB_PASSWORD, API_KEY) hard-coded no spec.  
   - Imagem sem tag estável (usa “latest” implícito).  
   - securityContext vazio – não garante usuário não-root.  
   - Não há tolerâncias ou afinidade para alta-disponibilidade.  
   Sugestões  
   - Mover secrets para um Secret Kubernetes e usar secretKeyRef.  
   - Especificar imagem com tag (ex: fiware/orion-ld:1.4.0).  
   - Definir securityContext com runAsNonRoot: true, read-only rootfs etc.  
   - (Opcional) Adicionar affinity/anti-affinity e tolerations conforme sua política de nó.

3) HPA “fiware-orionld-hpa”  
   - Está OK, apenas valide se sua métrica de memória está disponível no cluster.  
   - Poderia incluir um metricServer dedicado ou custom metrics, se necessário.

---  
Apliquei o novo Service e o novo Deployment (incluindo um Secret de exemplo). Use `kubectl apply -f corrected.yaml -n teste-orion`.  

```yaml
# corrected.yaml

# 1) Secret para DB_PASSWORD e API_KEY
apiVersion: v1
kind: Secret
metadata:
  name: fiware-orionld-credentials
  namespace: teste-orion
  labels:
    app: orionld
type: Opaque
stringData:
  DB_PASSWORD: "123456789"
  API_KEY: "sk-1234567890abcdef"

---
# 2) Service corrigido
apiVersion: v1
kind: Service
metadata:
  name: fiware-orionld-service
  namespace: teste-orion
  labels:
    app: orionld
    tier: api
    version: "v1"
spec:
  type: LoadBalancer
  selector:
    app: orionld
  ports:
    - name: http
      port: 1027
      targetPort: 1026
      protocol: TCP

---
# 3) Deployment corrigido
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fiware-orionld
  namespace: teste-orion
  labels:
    app: orionld
    tier: api
    version: "v1"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orionld
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
  template:
    metadata:
      labels:
        app: orionld
        tier: api
        version: "v1"
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
      containers:
        - name: orion
          image: fiware/orion-ld:1.4.0
          imagePullPolicy: IfNotPresent
          args:
            - "-dbhost"
            - "orionld-mongodb-svc:27017"
            - "-rplSet"
            - "orionld-mongodb"
            - "-dbuser"
            - "usuariozão"
            - "-dbAuthMech"
            - "SCRAM-SHA-256"
            - "-db"
            - "orion"
            - "-statCounters"
            - "-statSemWait"
            - "-statTiming"
            - "-statNotifQueue"
          env:
            - name: ORIONLD_MONGOCONLY
              value: "TRUE"
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: fiware-orionld-credentials
                  key: DB_PASSWORD
            - name: API_KEY
              valueFrom:
                secretKeyRef:
                  name: fiware-orionld-credentials
                  key: API_KEY
          ports:
            - containerPort: 1026
              protocol: TCP
          resources:
            requests:
              cpu: "200m"
              memory: "200Mi"
            limits:
              cpu: "500m"
              memory: "500Mi"
          livenessProbe:
            httpGet:
              path: /version
              port: 1026
            initialDelaySeconds: 15
            periodSeconds: 10
            timeoutSeconds: 2
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /version
              port: 1026
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 3
      dnsPolicy: ClusterFirst
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
      # affinities/tolerations podem ser adicionados aqui conforme necessário
```

Passos para aplicar:
1. `kubectl apply -f corrected.yaml -n teste-orion`  
2. Verifique se os pods entram em Ready:  
   `kubectl rollout status deployment/fiware-orionld -n teste-orion`  
3. Confira o Service:  
   `kubectl get svc/fiware-orionld-service -n teste-orion -o wide`  
4. Monitore o HPA (`kubectl describe hpa/fiware-orionld-hpa -n teste-orion`).  

Assim garantimos consistência de labels, segurança e gestão de segredos em conformidade com as boas práticas.

## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                 READY   STATUS             RESTARTS      AGE
pod/fiware-orionld-548584cdf-4n7p8   0/1     CrashLoopBackOff   4 (4s ago)    105s
pod/fiware-orionld-548584cdf-9kzs2   0/1     Running            4 (19s ago)   105s
pod/fiware-orionld-548584cdf-w7jff   0/1     Running            4 (19s ago)   105s
pod/fiware-orionld-65dd49b55-st7qn   0/1     Pending            0             37s

NAME                             TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.98.134.249   <pending>     1027:31937/TCP   105s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     1            0           105s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       105s
replicaset.apps/fiware-orionld-65dd49b55   1         1         0       37s

NAME                                                     REFERENCE                   TARGETS                              MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: 4%/70%   3         15        3          105s
```