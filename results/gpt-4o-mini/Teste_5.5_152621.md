# Relatório: 5-nginx.yaml - Rep 5

## Status Final: ❌ FALHA
**Veredito:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

---

## 🔍 Análise
Os recursos foram corrigidos e aplicados com sucesso no namespace `teste-nginx`. 

1. O **Serviço** `nginxsvc` foi recriado.
2. O **ReplicationController** `my-nginx` foi recriado.

Se precisar de mais alguma coisa ou de mais verificações, estou à disposição!

## 🛠️ Fix Aplicado
```yaml
Os recursos foram corrigidos e aplicados com sucesso no namespace `teste-nginx`. 

1. O **Serviço** `nginxsvc` foi recriado.
2. O **ReplicationController** `my-nginx` foi recriado.

Se precisar de mais alguma coisa ou de mais verificações, estou à disposição!
```

## 📋 Cluster Snapshot
```
NAME                 READY   STATUS              RESTARTS   AGE
pod/my-nginx-5gmjw   0/1     ContainerCreating   0          2m3s
pod/my-nginx-d8hkp   0/1     ContainerCreating   0          2m39s

NAME                             DESIRED   CURRENT   READY   AGE
replicationcontroller/my-nginx   1         1         0       2m3s

NAME               TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)                      AGE
service/nginxsvc   NodePort   10.97.159.49   <none>        80:30543/TCP,443:31696/TCP   2m19s
```