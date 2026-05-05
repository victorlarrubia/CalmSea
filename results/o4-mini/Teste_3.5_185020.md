# Relatório de Benchmark: 3-mysql.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 5
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Seguem, primeiro, os principais problemas detectados no “Pod mysql” original e em sua configuração de produção, com a correção recomendada em cada caso. Em seguida, o manifesto final de Deployment e Service aplicado no namespace `teste-mysql`.

1) Uso de Pod em vez de Deployment  
   – Problema: não há gestão de réplicas, estratégias de rollout nem auto-recuperação em falhas.  
   – Correção: migrar para um Deployment com `replicas: >1` (ou 1 mínimo) e estratégia RollingUpdate.

2) Senhas hardcoded nas variáveis de ambiente  
   – Problema: exposição de credenciais sensíveis no YAML.  
   – Correção: mover MYSQL_ROOT_PASSWORD, MYSQL_USER e MYSQL_PASSWORD para um Secret Kubernetes e referenciar via `envFrom` ou `valueFrom.secretKeyRef`.

3) Imagem sem tag e nome incorreto  
   – Problema: `image: my-sql` (provavelmente não existe) e sem tag fixa (`latest` muda sem controle).  
   – Correção: usar `image: mysql:8.0.33` (por exemplo) ou outra versão imutável.

4) Ausência de liveness/readiness probes  
   – Problema: sem probes, o Kube não sabe quando reiniciar ou enviar tráfego ao pod.  
   – Correção: adicionar probes TCP ou HTTP (no caso do MySQL, um comando exec ou tcpSocket na porta 3306).

5) Recursos e limites  
   – Problema: request = limit de CPU; melhor trabalhar com request < limit e definir burst.  
   – Correção: por exemplo, `requests: cpu 250m / memory 256Mi` e `limits: cpu 500m / memory 512Mi`.

6) Labels e selectors inconsistentes  
   – Problema: só havia `metadata.labels.name=mysql`.  
   – Correção: unificar com `app: mysql` e usar o mesmo selector no Service/Deployment.

7) Ausência de `securityContext`  
   – Problema: pods rodam como root por padrão.  
   – Correção: `runAsUser: 1000`, `fsGroup: 1000`, `runAsNonRoot: true`, `allowPrivilegeEscalation: false`.

8) Volume Cinder direto em Pod  
   – Problema: não há PVC, apenas volume Cinder embutido.  
   – Correção: usar PersistentVolumeClaim (existe `mysql-pvc`) e referenciar no Deployment.

———  
MANIFESTO APLICADO (namespace teste-mysql)

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: mysql-service
  namespace: teste-mysql
  labels:
    app: mysql
spec:
  type: ClusterIP
  selector:
    app: mysql
  ports:
    - name: mysql
      port: 3306
      targetPort: 3306
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql-deployment
  namespace: teste-mysql
  labels:
    app: mysql
spec:
  replicas: 1
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
      annotations:
        prometheus.io/scrape: "false"
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: mysql
        image: mysql:8.0.33
        imagePullPolicy: IfNotPresent
        ports:
          - containerPort: 3306
            name: mysql
            protocol: TCP
        env:
          - name: MYSQL_ROOT_PASSWORD
            valueFrom:
              secretKeyRef:
                name: mysql-secret
                key: root-password
          - name: MYSQL_USER
            valueFrom:
              secretKeyRef:
                name: mysql-secret
                key: user
          - name: MYSQL_PASSWORD
            valueFrom:
              secretKeyRef:
                name: mysql-secret
                key: password
          - name: MYSQL_DATABASE
            value: production_db
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        readinessProbe:
          exec:
            command:
              - sh
              - -c
              - mysqladmin ping -h 127.0.0.1 -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}"
          initialDelaySeconds: 15
          periodSeconds: 10
          timeoutSeconds: 5
        livenessProbe:
          tcpSocket:
            port: 3306
          initialDelaySeconds: 30
          periodSeconds: 20
        volumeMounts:
          - name: data
            mountPath: /var/lib/mysql
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: mysql-pvc
```

Breve justificativa das escolhas principais:  
• Deployment + RollingUpdate → Zero-downtime.  
• Secret para credenciais.  
• Versão de imagem fixa.  
• Probes para saúde.  
• Resources separados (requests < limits).  
• SecurityContext para rodar sem privilégios.  
• PVC para persistência.  

Com isso, passamos a um setup mais resiliente, seguro e alinhado às boas práticas de produção.

## 📋 Estado Final do Namespace (teste-mysql)
```
NAME                                    READY   STATUS    RESTARTS   AGE
pod/mysql-deployment-66777c9d45-2cx7h   0/1     Pending   0          2m17s

NAME                    TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
service/mysql-service   ClusterIP   10.97.100.85   <none>        3306/TCP   2m18s

NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/mysql-deployment   0/1     1            0           2m18s

NAME                                          DESIRED   CURRENT   READY   AGE
replicaset.apps/mysql-deployment-66777c9d45   1         1         0       2m18s
```