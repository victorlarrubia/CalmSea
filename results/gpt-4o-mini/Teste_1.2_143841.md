# Relatório: 1-orion.yaml - Rep 2

## Status Final: ❌ FALHA
**Veredito:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

---

## 🔍 Análise
Os recursos foram deletados e recriados com sucesso no namespace `teste-orion`. O Deployment `fiware-orionld` e o Service `fiware-orionld-service` foram restaurados. 

Se precisar de mais alguma coisa ou de mais informações, estou à disposição!

## 🛠️ Fix Aplicado
```yaml
Os recursos foram deletados e recriados com sucesso no namespace `teste-orion`. O Deployment `fiware-orionld` e o Service `fiware-orionld-service` foram restaurados. 

Se precisar de mais alguma coisa ou de mais informações, estou à disposição!
```

## 📋 Cluster Snapshot
```
NAME                                 READY   STATUS    RESTARTS   AGE
pod/fiware-orionld-548584cdf-9blwr   0/1     Running   0          10s
pod/fiware-orionld-548584cdf-jwgjf   0/1     Running   0          10s
pod/fiware-orionld-548584cdf-lzsj9   0/1     Running   0          10s

NAME                             TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.100.55.71   <pending>     1027:32140/TCP   10s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           10s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       10s

NAME                                                     REFERENCE                   TARGETS                                     MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: <unknown>/70%   3         15        0          10s
```