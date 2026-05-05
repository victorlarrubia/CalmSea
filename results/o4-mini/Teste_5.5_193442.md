# Relatório de Benchmark: 5-nginx.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 5
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Aqui está a análise dos recursos e as correções recomendadas:

1) Service (nginxsvc)
   - Tipo NodePort expõe portas altas (31690, 30138); em produção, prefira LoadBalancer ou Ingress.
   - Annotation “last-applied-configuration” desatualizada, com annotations vazias.
   - Recomendações:
     a) Altere spec.type para LoadBalancer (se suportado) ou mantenha ClusterIP e use Ingress.
     b) Adicione health check externalTrafficPolicy: Local para preservar client IP.
     c) Inclua labels adicionais (app.kubernetes.io/name/environment).

2) Pod (via ReplicationController my-nginx)
   Problemas:
   - Uso de ReplicationController obsoleto: recomendação migrar para Deployment.
   - Label “app”: “nginxs” difere do service “nginx” => selector mismatch potencial.
   - resources {} sem requests/limits: arriscado em produção.
   - Variáveis de ambiente sensíveis (SSL_CERT_PASSWORD, DB_CONNECTION) expostas em plain text.
   - Comando “/hom/auto-reload-nginx.sh” possivelmente typo (/hom vs /home).
   - image “ymqytw/nginxhttps” sem tag de versão.
   - Falta readinessProbe.
   - Permissões de segurança não configuradas (securityContext vazio).
   - volumeMounts: montagem de secret direto no pod; talvez usar CSI driver.

Sugestão de correção: migrar RC para Deployment com:

apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-nginx
  namespace: teste-nginx
  labels:
    app.kubernetes.io/name: nginx
    app.kubernetes.io/component: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginxhttps
        image: ymqytw/nginxhttps:v1.0.0
        imagePullPolicy: IfNotPresent
        command: ["/home/auto-reload-nginx.sh"]
        env:
        - name: SSL_CERT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: nginxsecret
              key: sslCertPassword
        - name: DB_CONNECTION
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: connectionString
        ports:
        - containerPort: 80
          name: http
        - containerPort: 443
          name: https
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
        readinessProbe:
          httpGet:
            path: /index.html
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /index.html
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 30
          failureThreshold: 3
        volumeMounts:
        - name: secret-volume
          mountPath: /etc/nginx/ssl
          readOnly: true
        - name: configmap-volume
          mountPath: /etc/nginx/conf.d
      volumes:
      - name: secret-volume
        secret:
          secretName: nginxsecret
          defaultMode: 420
      - name: configmap-volume
        configMap:
          name: nginxconfigmap
          defaultMode: 420
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000

3) Atualização no cluster
   - Delete ReplicationController (já deletado).
   - Aplicar novo Service modificado e o Deployment sugerido.
   - Utilize client-side dry-run antes: kubectl apply --dry-run=client.

Vamos aplicar as alterações:

1) Service com LoadBalancer e annotations:
   (segue YAML)

2) Deployment conforme acima.

Confirma aplicar?

## 📋 Estado Final do Namespace (teste-nginx)
```
NAME                 READY   STATUS              RESTARTS   AGE
pod/my-nginx-k75kq   0/1     ContainerCreating   0          3m14s

NAME               TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
service/nginxsvc   NodePort   10.104.37.229   <none>        80:31690/TCP,443:30138/TCP   3m14s
```