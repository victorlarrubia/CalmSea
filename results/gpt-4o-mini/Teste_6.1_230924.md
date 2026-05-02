# Relatório: 6-selenium.yaml - Rep 1

## Status Final: ✅ SUCESSO
**Veredito:** Sucesso: Ambiente íntegro e estável

---

## 🔍 Análise
Os recursos foram deletados com sucesso e o novo Deployment e Service para o Selenium Hub foram aplicados corretamente no namespace `teste-selenium`. 

Aqui estão as correções que foram feitas:

1. **Deployment**:
   - O Deployment foi recriado com as configurações corretas, incluindo probes de liveness e readiness, e a política de pull da imagem foi definida como `Always`.

2. **Service**:
   - O Service foi recriado com a correção do seletor, que agora está corretamente referenciando `app: selenium-hub` em vez de `app: sellenium-hub`.

Se precisar de mais alguma coisa ou de mais ajustes, estou à disposição!

## 🛠️ Fix Aplicado
```yaml
Os recursos foram deletados com sucesso e o novo Deployment e Service para o Selenium Hub foram aplicados corretamente no namespace `teste-selenium`. 

Aqui estão as correções que foram feitas:

1. **Deployment**:
   - O Deployment foi recriado com as configurações corretas, incluindo probes de liveness e readiness, e a política de pull da imagem foi definida como `Always`.

2. **Service**:
   - O Service foi recriado com a correção do seletor, que agora está corretamente referenciando `app: selenium-hub` em vez de `app: sellenium-hub`.

Se precisar de mais alguma coisa ou de mais ajustes, estou à disposição!
```

## 📋 Cluster Snapshot
```
NAME                                READY   STATUS    RESTARTS   AGE
pod/selenium-hub-5568fdc774-zptks   1/1     Running   0          39s

NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/selenium-hub   1/1     1            1           39s

NAME                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/selenium-hub-5568fdc774   1         1         1       39s
```