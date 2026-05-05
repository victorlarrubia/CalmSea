# Relatório de Benchmark: 7-elasticsearch.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 2
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
A seguir o diagnóstico dos recursos atuais e as recomendações para deixá-los alinhados com as boas práticas de produção.   

1) Inconsistência de labels e selectors  
   - Serviço “elasticsearch” (tipo LoadBalancer) usa selector “component: elasticsearch”  
   - StatefulSet / Deployment criado usam label “app: elasticsearch”  
   ⇒ Resultado: o Service nunca vai “enxergar” os Pods.  
   Sugestão de correção: padronizar todas as labels/selectors para `app: elasticsearch`.  

2) Uso simultâneo de ReplicationController e StatefulSet/Deployment  
   - Você declarou um RC “es” mas acabou aplicando um StatefulSet “elasticsearch”  
   ⇒ Sobrecarga de responsabilidades e possível conflito de escalonamento.  
   Sugestão de correção: remover o RC “es” se for adotar StatefulSet.  

3) Campos não permitidos em patch de StatefulSet  
   - Erro “updates to statefulset spec for fields other than ‘replicas’, … are forbidden”  
   - O campo `topologySpreadConstraints` aparece como “unknown field”: sua versão de API não suporta (antiga)  
   ⇒ Para alterar spec “template” (ex. adicionar affinity, probes ou topoSpread) é preciso recriar o StatefulSet ou usar um rollout in-place que altere apenas o template.  
   Sugestão de correção:  
     a) Remover os campos não suportados (ou atualizar cluster para versão >= 1.21).  
     b) Se precisar recriar, delete o StatefulSet (mantendo PVC) e aplique o novo manifest com a spec consolidada.  

4) Boas práticas adicionais para Elasticsearch em produção  
   - Especificar sempre requests e limits de cpu/mem.  
   - Garantir readinessProbe que aguarde o cluster ficar verde.  
   - Usar headless Service para nodes-transport e Service LoadBalancer só para HTTP.  
   - Definir `podAntiAffinity` para distribuir Pods em nós diferentes.  
   - Configurar `persistentVolumeClaimRetentionPolicy` se precisar reter dados em delete.  

-----------------------------------------------------------------------------  
Manifests consolidados para aplicação (namespace: teste-elasticsearch)  

1) Service HTTP (LoadBalancer)  
```yaml
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
      protocol: TCP
      targetPort: 9200
  externalTrafficPolicy: Cluster
```

2) Service Transport (headless)  
```yaml
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch-transport
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
      protocol: TCP
      targetPort: 9300
```

3) StatefulSet Elasticsearch  
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: teste-elasticsearch
  labels:
    app: elasticsearch
spec:
  serviceName: elasticsearch-transport   # headless
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
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app: elasticsearch
              topologyKey: kubernetes.io/hostname
      containers:
        - name: elasticsearch
          image: docker.elastic.co/elasticsearch/elasticsearch:8.9.0
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 9200
            - name: transport
              containerPort: 9300
          env:
            - name: node.name
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: cluster.name
              value: es-cluster-prod
            - name: discovery.seed_hosts
              value: "elasticsearch-transport"
            - name: ES_JAVA_OPTS
              value: "-Xms1g -Xmx1g"
          resources:
            requests:
              cpu: 500m
              memory: 2Gi
            limits:
              cpu: 1
              memory: 4Gi
          readinessProbe:
            httpGet:
              path: /_cluster/health?local=true
              port: 9200
            initialDelaySeconds: 20
            periodSeconds: 10
            timeoutSeconds: 5
          livenessProbe:
            httpGet:
              path: /_nodes/_local
              port: 9200
            initialDelaySeconds: 30
            periodSeconds: 15
            timeoutSeconds: 5
          volumeMounts:
            - name: data
              mountPath: /usr/share/elasticsearch/data
  volumeClaimTemplates:
    - metadata:
        name: data
        annotations:
          volume.beta.kubernetes.io/storage-class: fast-storage
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 50Gi
```

Passos de aplicação segura:  
1. `kubectl -n teste-elasticsearch delete rc es`  
2. `kubectl -n teste-elasticsearch apply -f elasticsearch-http.yaml`  
3. `kubectl -n teste-elasticsearch apply -f elasticsearch-transport.yaml`  
4. `kubectl -n teste-elasticsearch delete statefulset elasticsearch --cascade=orphan`  
   (mantém PVCs)  
5. `kubectl -n teste-elasticsearch apply -f elasticsearch-statefulset.yaml`  

Dessa forma você garante um rollout limpo, sem tentar patchar campos proibidos, e segue as melhores práticas para um cluster de Elasticsearch em produção.

## 📋 Estado Final do Namespace (teste-elasticsearch)
```
NAME                                 READY   STATUS    RESTARTS   AGE
pod/elasticsearch-0                  0/1     Pending   0          3m18s
pod/elasticsearch-6bf98bd5b8-49vgs   0/1     Pending   0          5m40s
pod/elasticsearch-6bf98bd5b8-m4ksj   0/1     Pending   0          5m40s
pod/elasticsearch-6bf98bd5b8-vzzg4   0/1     Pending   0          5m40s

NAME                       DESIRED   CURRENT   READY   AGE
replicationcontroller/es   1         0         0       6m29s

NAME                              TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)                         AGE
service/elasticsearch             LoadBalancer   10.96.252.6   <pending>     9200:31568/TCP,9300:31395/TCP   6m29s
service/elasticsearch-transport   ClusterIP      None          <none>        9300/TCP                        5m18s

NAME                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/elasticsearch   0/3     3            0           5m40s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/elasticsearch-6bf98bd5b8   3         3         0       5m40s

NAME                             READY   AGE
statefulset.apps/elasticsearch   0/3     3m18s
```