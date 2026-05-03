# Relatório: 6-selenium.yaml - Rep 3

## Status Final: ✅ SUCESSO
**Veredito:** Sucesso: Ambiente íntegro e estável

---

## 🔍 Análise
Os recursos foram deletados com sucesso e o novo Deployment e Service para o Selenium Hub foram aplicados no namespace `teste-selenium`. 

Aqui estão as correções que foram feitas:

1. **Deployment**:
   - O Deployment foi recriado com as configurações corretas, incluindo probes de liveness e readiness adequadas, e a política de pull da imagem foi definida como `Always`.

2. **Service**:
   - O Service foi recriado, corrigindo o erro de digitação no seletor (de `sellenium-hub` para `selenium-hub`).

Se precisar de mais alguma coisa ou de mais ajustes, estou à disposição!

## 🛠️ Fix Aplicado
```yaml
Os recursos foram deletados com sucesso e o novo Deployment e Service para o Selenium Hub foram aplicados no namespace `teste-selenium`. 

Aqui estão as correções que foram feitas:

1. **Deployment**:
   - O Deployment foi recriado com as configurações corretas, incluindo probes de liveness e readiness adequadas, e a política de pull da imagem foi definida como `Always`.

2. **Service**:
   - O Service foi recriado, corrigindo o erro de digitação no seletor (de `sellenium-hub` para `selenium-hub`).

Se precisar de mais alguma coisa ou de mais ajustes, estou à disposição!
```

## 📋 Cluster Snapshot
```
NAME                                READY   STATUS    RESTARTS   AGE
pod/selenium-hub-5568fdc774-k96t4   1/1     Running   0          34s

NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/selenium-hub   1/1     1            1           34s

NAME                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/selenium-hub-5568fdc774   1         1         1       34s
```