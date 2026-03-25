# Teste 2-frontend.yaml - Rep 2

## Análise
Segue a lista de problemas e más-práticas detectadas neste Deployment:

1. Imagem incorreta/tipo  
   - image: “nginxs” (provavelmente um typo de “nginx”). Isso vai impedir o pull/resolução da imagem.

2. Segredos em texto claro  
   - A variável PASSWORD_SERVICE_HOST carrega uma senha (“123456”) em claro dentro do manifesto.  
   - Recomenda-se usar um Secret (e referenciá-lo via envFrom ou valueFrom).

3. Falta de resource limits  
   - Há apenas requests (cpu/memory), mas não há limits.  
   - Sem limits, um pod mal-comportado pode consumir todo o recurso do nó.

4. Ausência de probes (liveness/readiness)  
   - Sem liveness ou readiness probes, falhas de aplicação podem não ser detectadas pelo Kubelet e o rollout fica imprevisível.

5. Replica única em produção  
   - replicas: 1 não traz tolerância a falhas; ideal mínimo 2 para alta disponibilidade.

6. Segurança de container não configurada  
   - Não há securityContext no Pod nem no container:  
     • runAsNonRoot  
     • readOnlyRootFilesystem  
     • dropCapabilities  
   - Por padrão o container roda como root, ampliando superfície de ataque.

7. imagePullPolicy  
   - Não definido; em produção recomenda-se explicitamente “Always” para garantir pull de novas tags.

8. Conta de serviço e RBAC  
   - Usa a ServiceAccount default.  
   - Em produção, crie e vincule uma conta de serviço com RBAC mínimo.

9. Ausência de NetworkPolicy  
   - Sem NetworkPolicy, todo tráfego (ingress/egress) do Pod fica liberado dentro do namespace.

10. Faltam labels de versão/ambiente  
    - Útil para rollout controlado e auditoria (ex: version: v1.2, env: prod).

Recomendações gerais:  
• Corrigir nome da imagem.  
• Extrair segredos para Secret.  
• Definir requests e limits.  
• Incluir liveness/readiness probes.  
• Adotar securityContext com princípios de menor privilégio.  
• Versionar e taggear adequadamente suas imagens.  
• Provisionar ao menos 2 réplicas em produção.  
• Criar ServiceAccount customizada e roles específicas.  
• Definir NetworkPolicies para restringir tráfego.

## Fix
✅ **Executado apply_manifest:**

```json
🚀 **Aplicado:** {'status': 'success', 'message': 'Sucesso:\nsecret/guestbook-credentials created\ndeployment.apps/frontend configured\n'}
```

## K8s
```
NAME                        READY   STATUS              RESTARTS   AGE
frontend-65d44dd469-rrs7c   0/1     ImagePullBackOff    0          27s
frontend-865c976f6-btlfm    0/1     ContainerCreating   0          0s
```