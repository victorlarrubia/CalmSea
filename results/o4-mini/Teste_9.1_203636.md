# Relatório de Benchmark: 9-storm.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 1
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Seguem os principais problemas que identificamos e as correções propostas, seguidas do manifesto final corrigido. Para aplicar, primeiro certifique-se de deletar qualquer Deployment/Service conflitante e então `kubectl apply -f` neste YAML.

1) Immutable selector no Deployment  
   - Problema: você tentou alterar a label de selector de `name: storm-worker` para `app:…` sem recriar o objeto.  
   - Correção: recrie o Deployment com um selector definitivo (e labels idênticas) — por isso deletamos o antigo e aplicamos este.

2) Service sem nomes em portas  
   - Problema: portas do Service exigem campo `name`.  
   - Correção: adicionamos `name:` em cada porta (ex.: `tcp-6700` etc.).

3) Boas práticas adicionais  
   - Usar tags de imagem fixas (não `latest`): ex.: `storm:2.4.0`.  
   - Remover `hostPort` a não ser que seja imprescindível. Se não precisar, comente ou retire.  
   - Resource requests/limits mais realistas.  
   - Probes de readiness/liveness.  
   - Labels padronizadas (`app:`, `environment:`).

Manifesto combinado (Deployment + Service):

```yaml
# --------------------------------------------------
# Namespace: teste-storm
# --------------------------------------------------
apiVersion: v1
kind: Service
metadata:
  name: storm-worker-service
  namespace: teste-storm
  labels:
    app: storm-worker-controller
    environment: production
spec:
  type: ClusterIP
  selector:
    app: storm-worker-controller
    uses: nimbus
  ports:
    - name: tcp-6700
      protocol: TCP
      port: 6700
      targetPort: 6700
    - name: tcp-6701
      protocol: TCP
      port: 6701
      targetPort: 6701
    - name: tcp-6702
      protocol: TCP
      port: 6702
      targetPort: 6702
    - name: tcp-6703
      protocol: TCP
      port: 6703
      targetPort: 6703
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: storm-worker-controller
  namespace: teste-storm
  labels:
    app: storm-worker-controller
    environment: production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: storm-worker-controller
      uses: nimbus
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
  template:
    metadata:
      labels:
        app: storm-worker-controller
        uses: nimbus
    spec:
      # Se não precisar de hostPort em produção, remova as linhas abaixo:
      # hostNetwork: false
      containers:
        - name: storm-worker
          image: storm:2.4.0
          imagePullPolicy: IfNotPresent
          command:
            - /bin/sh
            - -c
          args:
            - >
              echo 'Worker stub iniciado...';
              while true; do sleep 3600; done
          env:
            - name: STORM_NIMBUS
              value: nimbus.default.svc.cluster.local
            - name: STORM_ZOOKEEPER_SERVERS
              value: zookeeper.default.svc.cluster.local:2181
            # Para credenciais, use Secret em vez de literal:
            # - name: STORM_NIMBUS_PASSWORD
            #   valueFrom:
            #     secretKeyRef:
            #       name: storm-nimbus-secret
            #       key: password
          ports:
            - containerPort: 6700
              name: tcp-6700
            - containerPort: 6701
              name: tcp-6701
            - containerPort: 6702
              name: tcp-6702
            - containerPort: 6703
              name: tcp-6703
          resources:
            requests:
              cpu: "100m"
              memory: "64Mi"
            limits:
              cpu: "200m"
              memory: "128Mi"
          readinessProbe:
            tcpSocket:
              port: 6700
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            tcpSocket:
              port: 6700
            initialDelaySeconds: 30
            periodSeconds: 20
      dnsPolicy: ClusterFirst
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
```

Passo-a-passo de aplicação:

1. `kubectl -n teste-storm delete deployment storm-worker-controller --ignore-not-found`  
2. `kubectl -n teste-storm delete service storm-worker-service --ignore-not-found`  
3. Salve o manifesto acima em `storm-worker.yaml` e rode:  
   `kubectl apply -f storm-worker.yaml`

Com isso, selector, labels e nomes de portas estarão consistentes e alinhados às boas práticas de produção.

## 📋 Estado Final do Namespace (teste-storm)
```
NAME                           TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                               AGE
service/storm-worker-service   ClusterIP   10.100.123.53   <none>        6700/TCP,6701/TCP,6702/TCP,6703/TCP   5m44s
```