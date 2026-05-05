# Relatório de Benchmark: 4-vllm.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 1
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
A seguir o diagnóstico dos principais pontos de melhoria e a proposta de correção completa (Deployment + Service). Como a `spec.selector` do Deployment é imutável, você precisará primeiro deletar o `Deployment` antigo e só então aplicar o novo manifesto.

1) Misconfigurações identificadas  
- Comando inválido: você está chamando “python5” num container que usa “python:3.9-slim”.  
- Variáveis sensíveis em claro (`HUGGING_FACE_HUB_TOKEN`, `ADMIN_PASSWORD`).  
- Falta de probes de liveness/readiness – sem elas o Kubernetes não sabe quando o pod está pronto ou saudável.  
- Rótulos inconsistentes: selector/labels eram `app: gemma-server`, mas você tentou migrar para `app.kubernetes.io/name=vllm-gemma`.  
- Tag de imagem “flutuante” sem digest ou versão imutável.  
- Falta de securityContext que garanta execução non-root.  

2) Fluxo de aplicação sugerido  
   a) Criar/atualizar um Secret com as credenciais.  
   b) `kubectl delete deployment vllm-gemma-deployment -n teste-vllm`  
   c) `kubectl apply -f vllm-gemma-manifest.yaml -n teste-vllm`  

3) Manifesto corrigido  

```yaml
---
apiVersion: v1
kind: Secret
metadata:
  name: vllm-gemma-credentials
  namespace: teste-vllm
  labels:
    app.kubernetes.io/name: vllm-gemma
type: Opaque
stringData:
  HUGGING_FACE_HUB_TOKEN: hf_hardcoded_token_abc123xyz
  ADMIN_PASSWORD: admin123!@#
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-gemma-deployment
  namespace: teste-vllm
  labels:
    app.kubernetes.io/name: vllm-gemma
    app.kubernetes.io/instance: gemma
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: vllm-gemma
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
  template:
    metadata:
      labels:
        app.kubernetes.io/name: vllm-gemma
        app.kubernetes.io/instance: gemma
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
        - name: inference-server
          image: python:3.9-slim@sha256:<DIGEST_AQUI>
          imagePullPolicy: IfNotPresent
          command: ["sh", "-c"]
          args:
            - |
              echo "Mock vLLM server for testing"
              python3 -m http.server 8080
          ports:
            - name: http
              containerPort: 8080
              protocol: TCP
          env:
            - name: MODEL_ID
              value: mock-model-for-testing
            - name: HUGGING_FACE_HUB_TOKEN
              valueFrom:
                secretKeyRef:
                  name: vllm-gemma-credentials
                  key: HUGGING_FACE_HUB_TOKEN
            - name: ADMIN_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: vllm-gemma-credentials
                  key: ADMIN_PASSWORD
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 200m
              memory: 256Mi
          readinessProbe:
            httpGet:
              path: "/"
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: "/"
              port: http
            initialDelaySeconds: 15
            periodSeconds: 20
          volumeMounts:
            - name: dshm
              mountPath: /dev/shm
      volumes:
        - name: dshm
          emptyDir:
            medium: Memory
            sizeLimit: 64Mi
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-gemma-service
  namespace: teste-vllm
  labels:
    app.kubernetes.io/name: vllm-gemma
    app.kubernetes.io/instance: gemma
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: vllm-gemma
  ports:
    - name: http
      port: 80
      targetPort: http
      protocol: TCP
```

Passos finais:

1. `kubectl delete deployment vllm-gemma-deployment -n teste-vllm`
2. `kubectl apply -f vllm-gemma-manifest.yaml -n teste-vllm`

Isso resolve:
- Imutabilidade de selector (ao recriar o Deployment).
- Uso de Secret para credenciais.
- Probes de saúde.
- Labels padronizados.
- Comando corrigido para Python 3.
- Execução non‐root.
- Volumes em memória seguros.

## 📋 Estado Final do Namespace (teste-vllm)
```
NAME                                         READY   STATUS    RESTARTS   AGE
pod/vllm-gemma-deployment-6f85cf8967-796jh   0/1     Pending   0          3m20s
pod/vllm-gemma-deployment-7d9d876785-9drbz   0/1     Pending   0          2m28s
pod/vllm-gemma-deployment-85f5f8b94-p869z    0/1     Pending   0          3m59s

NAME                         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/vllm-gemma-service   ClusterIP   10.109.130.94   <none>        80/TCP    3m20s

NAME                                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/vllm-gemma-deployment   0/2     1            0           3m59s

NAME                                               DESIRED   CURRENT   READY   AGE
replicaset.apps/vllm-gemma-deployment-6f85cf8967   1         1         0       3m20s
replicaset.apps/vllm-gemma-deployment-7d9d876785   1         1         0       2m28s
replicaset.apps/vllm-gemma-deployment-85f5f8b94    1         1         0       3m59s
```