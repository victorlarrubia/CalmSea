# Relatório de Benchmark: 2-frontend.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 4
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod frontend-65d44dd469-qrjmj: ImagePullBackOff

## 🧠 Raciocínio do Agente
Conforme solicitado, fizemos um “snapshot” do Deployment frontend no namespace teste-frontend. Abaixo segue o diagnóstico dos principais pontos de melhoria e um manifesto corrigido (Deployment + Service + Secret) alinhado a boas práticas de produção.

1) Imagem sem tag e typo  
   • Problema: `image: nginxs` (typo) e sem versão fixa → impede rollbacks previsíveis.  
   • Correção: use `nginx:1.23.3-alpine` (ou outra versão semântica) e `imagePullPolicy: IfNotPresent`.

2) Variáveis de ambiente sensíveis “hard-coded”  
   • Problema: `PASSWORD_SERVICE_HOST=123456` fica exposto no Deployment.  
   • Correção: mover para Secret e referenciar via `envFrom`.

3) Falta de probes  
   • Problema: sem liveness/readiness, o Kube não detecta falhas.  
   • Correção: adicionar `livenessProbe` e `readinessProbe` HTTP.

4) Requests sem limites  
   • Problema: só há requests (`cpu:100m`, `memory:100Mi`), faltam limits → pode causar “noisy neighbor”.  
   • Correção: incluir ambos requests e limits (por ex. `limits: cpu:200m`, `memory:200Mi`).

5) Segurança do container  
   • Problema: rodando como root por omissão.  
   • Correção: `securityContext` com `runAsNonRoot: true`, `runAsUser:1000`, read-only root filesystem.

6) Labels e seletores  
   • Problema: carecem de convenções (ex.: app vs name).  
   • Correção: padronizar labels `app: frontend`, `tier: frontend`.

7) Service ausente inicialmente  
   • Já criamos um Service ClusterIP, mas reforçamos selector e ports.

---

### Manifesto consolidado (namespace: teste-frontend)

```yaml
---
apiVersion: v1
kind: Secret
metadata:
  name: frontend-secret
  namespace: teste-frontend
type: Opaque
stringData:
  password: "123456"     # ideal: usar helm/vault para gerenciar em production
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: teste-frontend
  labels:
    app: frontend
    tier: frontend
spec:
  type: ClusterIP
  selector:
    app: frontend
    tier: frontend
  ports:
    - name: http
      port: 80
      targetPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: teste-frontend
  labels:
    app: frontend
    tier: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
      tier: frontend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
  template:
    metadata:
      labels:
        app: frontend
        tier: frontend
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
      containers:
        - name: php-redis
          image: nginx:1.23.3-alpine
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 80
              protocol: TCP
          env:
            - name: PASSWORD_SERVICE_HOST
              valueFrom:
                secretKeyRef:
                  name: frontend-secret
                  key: password
          resources:
            requests:
              cpu: 100m
              memory: 100Mi
            limits:
              cpu: 200m
              memory: 200Mi
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 15
            periodSeconds: 20
            failureThreshold: 5
          securityContext:
            readOnlyRootFilesystem: true
      dnsPolicy: ClusterFirst
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
```

Próximos passos:
1. Faça um `kubectl apply -f frontend.yaml --namespace=teste-frontend --dry-run=client` para validar a sintaxe.  
2. Se tudo OK, `kubectl apply -f frontend.yaml`.  
3. Monitore `kubectl rollout status deployment/frontend -n teste-frontend`.  
4. Ajuste replicação conforme carga real e configure HorizontalPodAutoscaler quando estiver pronto.

Fico à disposição para qualquer dúvida ou ajuste adicional!

## 📋 Estado Final do Namespace (teste-frontend)
```
NAME                            READY   STATUS             RESTARTS   AGE
pod/frontend-5b48bc5f5c-hslfn   0/1     Pending            0          20s
pod/frontend-65d44dd469-qrjmj   0/1     ImagePullBackOff   0          97s
pod/frontend-6c7f988ff-k87fk    0/1     Pending            0          38s
pod/frontend-77bf4d899d-2twd9   0/1     Pending            0          53s

NAME               TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
service/frontend   ClusterIP   10.98.142.17   <none>        80/TCP    53s

NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/frontend   0/3     1            0           97s

NAME                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/frontend-5b48bc5f5c   1         1         0       21s
replicaset.apps/frontend-65d44dd469   1         1         0       97s
replicaset.apps/frontend-6c7f988ff    1         1         0       38s
replicaset.apps/frontend-77bf4d899d   1         1         0       53s
```