# Relatório: 1-orion.yaml - Rep 5

## Status Final: ❌ FALHA
**Veredito:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

---

## 🔍 Análise
Os recursos foram deletados e recriados com sucesso no namespace `teste-orion`. O Deployment `fiware-orionld` e o Service `fiware-orionld-service` foram criados novamente. 

Se precisar de mais alguma coisa, estou à disposição!

## 🛠️ Fix Aplicado
```yaml
Os recursos foram deletados e recriados com sucesso no namespace `teste-orion`. O Deployment `fiware-orionld` e o Service `fiware-orionld-service` foram criados novamente. 

Se precisar de mais alguma coisa, estou à disposição!
```

## 📋 Cluster Snapshot
```
NAME                                 READY   STATUS    RESTARTS      AGE
pod/fiware-orionld-d545c744f-65ktd   0/1     Running   4 (22s ago)   2m3s
pod/fiware-orionld-d545c744f-fs6g8   0/1     Running   4 (22s ago)   2m3s
pod/fiware-orionld-d545c744f-qrd7m   0/1     Running   4 (22s ago)   2m3s

NAME                             TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.106.117.182   <pending>     1027:31852/TCP   2m2s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           2m3s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-d545c744f   3         3         0       2m3s

NAME                                                     REFERENCE                   TARGETS                                     MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: <unknown>/70%   3         15        3          2m24s
```