# Relatório de Benchmark: 7-elasticsearch.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 5
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Segue diagnóstico dos principais bloqueios e sugestões de correção para levar o seu elasticsearch ao padrão de produção:

1) Service “elasticsearch”  
   - Problema: Você tentou alterar o campo `spec.clusterIPs`, que é imutável.  
   - Correção:  
     a) Para não ter conflito de IP, remova **sempre** o bloco `clusterIP/clusterIPs` do YAML antes de aplicar;  
     b) Se precisar recriar o Service mantendo o mesmo nome, faça:
        ```bash
        kubectl delete svc elasticsearch -n teste-elasticsearch
        kubectl apply -f service-elasticsearch.yaml -n teste-elasticsearch
        ```
     c) No YAML final, deixe o Kubernetes atribuir o `clusterIP`.

2) Novo design de Services  
   - Service HTTP (TCP/9200)  
   - Service Transport (TCP/9300)  
   - Headless Service (para descoberta de peers)  
   - Exemplo de `service-elasticsearch.yaml` corrigido:

```yaml
# service-elasticsearch.yaml
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch-http
  namespace: teste-elasticsearch
  labels:
    app: elasticsearch
spec:
  type: LoadBalancer
  selector:
    app: elasticsearch
  ports:
    - name: http
      port: 9200
      targetPort: 9200
---
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch-transport
  namespace: teste-elasticsearch
  labels:
    app: elasticsearch
spec:
  type: ClusterIP
  selector:
    app: elasticsearch
  ports:
    - name: transport
      port: 9300
      targetPort: 9300
---
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch-headless
  namespace: teste-elasticsearch
  labels:
    app: elasticsearch
spec:
  clusterIP: None
  selector:
    app: elasticsearch
  ports:
    - name: transport
      port: 9300
      targetPort: 9300
```

3) StatefulSet “elasticsearch”  
   - Problema: você alterou campos proibidos (ex.: `.spec.volumeClaimTemplates`, `.spec.serviceName`, etc.). O Kubernetes só permite mudanças em: `replicas`, `template`, `updateStrategy`, `revisionHistoryLimit`, `persistentVolumeClaimRetentionPolicy` e `minReadySeconds`.  
   - Correção:  
     a) Se precisar alterar campos imutáveis, faça delete+recreate do StatefulSet (atenção ao dado em disco!);  
     b) Opcionalmente, cloná-lo com outro nome e migrar dados;  
     c) Para produção, sugerimos incluir probes, resources, securityContext e storageClass:

```yaml
# statefulset-elasticsearch.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: teste-elasticsearch
  labels:
    app: elasticsearch
spec:
  serviceName: elasticsearch-headless
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  updateStrategy:
    type: RollingUpdate
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      securityContext:
        fsGroup: 1000
      containers:
        - name: elasticsearch
          image: docker.elastic.co/elasticsearch/elasticsearch:7.17.9
          ports:
            - containerPort: 9200
              name: http
            - containerPort: 9300
              name: transport
          env:
            - name: discovery.seed_hosts
              value: "elasticsearch-headless"
            - name: cluster.initial_master_nodes
              value: "elasticsearch-0,elasticsearch-1,elasticsearch-2"
          resources:
            requests:
              cpu: "500m"
              memory: "2Gi"
            limits:
              cpu: "1"
              memory: "4Gi"
          readinessProbe:
            httpGet:
              path: /
              port: 9200
            initialDelaySeconds: 20
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /
              port: 9200
            initialDelaySeconds: 60
            periodSeconds: 20
          volumeMounts:
            - name: data
              mountPath: /usr/share/elasticsearch/data
  volumeClaimTemplates:
    - metadata:
        name: data
        annotations:
          volume.beta.kubernetes.io/storage-class: fast-ssd
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 50Gi
```

4) Procedimento de rollout  
   1. Delete o StatefulSet atual (cuidando de backup dos PVCs, se necessários):
      `kubectl delete sts elasticsearch -n teste-elasticsearch`  
   2. Aplique o headless/service YAML:
      `kubectl apply -f service-elasticsearch.yaml -n teste-elasticsearch`  
   3. Crie o StatefulSet revisado:
      `kubectl apply -f statefulset-elasticsearch.yaml -n teste-elasticsearch`

Com isso você garante:  
- Boas práticas de labels/annotations consistentes  
- Requests & Limits definidos  
- Probes configuradas  
- Storage adequado e seguro  
- Serviço REST e transporte separados  
- Cluster discovery via headless service.

## 📋 Estado Final do Namespace (teste-elasticsearch)
```
NAME                  READY   STATUS    RESTARTS   AGE
pod/elasticsearch-0   0/1     Pending   0          3m7s

NAME                              TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
service/elasticsearch-headless    ClusterIP      None             <none>        9300/TCP         2m21s
service/elasticsearch-http        LoadBalancer   10.111.146.237   <pending>     9200:32209/TCP   3m7s
service/elasticsearch-transport   ClusterIP      10.108.124.21    <none>        9300/TCP         2m22s

NAME                             READY   AGE
statefulset.apps/elasticsearch   0/3     3m7s
```