# Teste 2-frontend.yaml - Rep 3

## Análise
Segue a lista de problemas e más práticas encontradas neste Deployment:

1. Imagem não versionada e possivelmente incorreta  
   - Foi especificada apenas “nginxs” (sem tag), o que dispara pull da tag “latest” por padrão.  
   - Falta pinagem de versão (ex.: `nginx:1.21.0@sha256:…`) e validação de assinatura de imagem.  
   - “nginxs” parece um typo/malicious; pode nunca existir ou apontar para repositório não confiável.

2. Ausência de securityContext  
   - Sem runAsNonRoot, runAsUser ou fsGroup: o container roda como root por padrão.  
   - Falta configuração de readOnlyRootFilesystem, capability drops (ex.: NET_RAW, SYS_ADMIN), SELinux/AppArmor profile.

3. Variável de ambiente sensível em claro  
   - `PASSWORD_SERVICE_HOST` armazena senha/credencial em texto plano no manifesto.  
   - Credenciais sensíveis devem ser gerenciadas via Secret (referenciado por envFrom/secretKeyRef).

4. Sem probes de saúde  
   - Não há livenessProbe nem readinessProbe – dificulta detecção de falhas e balanceamento de tráfego.

5. Falta de limites de recursos  
   - Apenas requests estão definidos; sem limits, container pode consumir memória/CPU ilimitada, afetando o nó.

6. Replica única  
   - `replicas: 1` não oferece tolerância a falhas; recomendável ter pelo menos 2 réplicas em produção.

7. Ausência de policy de rede (NetworkPolicy)  
   - Pod fica acessível sem restrições; não há isolamento de tráfego de/para outros pods/serviços.

8. Sem especificação de imagePullPolicy  
   - PullPolicy implícito em “IfNotPresent”; em produção costuma-se usar “Always” ou governance que garanta não usar cache inadvertidamente.

9. Selector de labels rígido demais  
   - Selector exige 2 labels (app + tier) – qualquer desalinhamento no template pode quebrar o Deployment.  
   - Atenção à consistência entre `matchLabels` e `template.metadata.labels`.

Recomendações de correção em alto nível:  
- Corrigir/impor versão da imagem; validar assinatura.  
- Adicionar securityContext (non-root, FS readonly, capabilities).  
- Mover senhas/segredos para Secret.  
- Definir readiness/liveness probes.  
- Especificar requests e limits de CPU/memória.  
- Aumentar réplicas para alta disponibilidade.  
- Implantar NetworkPolicies.  
- Definir imagePullPolicy adequada.  
- Revisar labels e selectors.

## Fix
✅ **Executado apply_manifest:**

```json
🚀 **Aplicado:** {'status': 'success', 'message': 'Sucesso:\ndeployment.apps/frontend configured\n'}
```

## K8s
```
NAME                        READY   STATUS              RESTARTS   AGE
frontend-65d44dd469-lm4vt   0/1     ErrImagePull        0          32s
frontend-685f94c7c5-5k4cl   0/1     ContainerCreating   0          0s
```