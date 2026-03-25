# Teste 1-orion.yaml - Rep 5

## Análise
Segue a lista de problemas e más práticas encontradas no manifesto fornecido:

1. Hard-coded credentials  
   - As variáveis de ambiente `DB_PASSWORD` e `API_KEY` (e o argumento `-dbpwd`) contêm segredos em texto puro.  
   - Recomenda-se usar Kubernetes Secrets e montá-los como variáveis ou volumes, jamais embedar senhas/token diretamente no Deployment.

2. Inconsistência de labels/selector do Service  
   - O Deployment rotula os pods com `app: orionld`, mas o Service seleciona `app: orionlds` (note o “s” extra).  
   - Consequência: o Service não encontra nenhum endpoint e fica sem pods ligados.

3. Falta de securityContext / execução como root  
   - Não há bloco `securityContext` no Pod nem no Container.  
   - Por padrão o container roda como root e permite escalation de privilégios.  
   - Deve-se definir pelo menos:
     • runAsNonRoot: true  
     • runAsUser: <UID não-root>  
     • securityContext.capabilities.drop: ["ALL"]  

4. Uso do ServiceAccount default  
   - Não há especificação de `serviceAccountName`, logo o pod usará o “default” com quaisquer RBAC atribuídas a ele.  
   - Melhor criar ServiceAccount próprio e vincular apenas as permissões estritamente necessárias.

5. Ausência de NetworkPolicy  
   - Sem políticas de rede, todo tráfego (intra-cluster e externo) flui livremente.  
   - Recomenda-se pelo menos um NetworkPolicy “deny-by-default” e abrir só o que for realmente necessário.

6. Imagem sem tag fixa (“latest” implícito)  
   - `image: fiware/orion-ld` puxa sempre a última versão, sem controle de versionamento.  
   - Utilize um tag semântico (por ex. `fiware/orion-ld:2.3.1`) para garantir reprodutibilidade e facilitar rollback.

7. Exposição direta por LoadBalancer sem TLS  
   - O Service é `type: LoadBalancer` num ambiente de produção, expondo a porta 1027 sem criptografia.  
   - Falta um Ingress ou TLS para proteger o canal de comunicação.

8. HPA com memory utilization no autoscaling/v2  
   - Embora CPU Utilization seja padrão, nem todas as versões de Kubernetes suportam `averageUtilization` para memória na API v2.  
   - Avaliar se o cluster aceita esse tipo de métrica ou usar `metrics/v2beta2` com `averageValue`.

9. Argumentos de linha de comando passam credenciais  
   - Além das variáveis de ambiente, o flag `-dbpwd` expõe a senha no comando de inicialização (visível em `ps` e logs do K8s).  
   - Melhores práticas: injetar usuário/senha via Secret e variável, evitando expor no args.

10. Ausência de afinidade/anti-afinidade  
    - Sem `affinity` ou `antiAffinity`, não há controle sobre a distribuição dos pods entre nós, afetando disponibilidade.

11. Probes muito agressivas ou genéricas  
    - `initialDelaySeconds` de 5–10 segundos pode não ser suficiente para inicialização em clusters carregados.  
    - Melhor validar timings e endpoints seguros (não usar `/version` em prod sem autenticação).

12. Caracteres não-ASCII no usuário do banco  
    - O valor `"usuariozão"` pode gerar problemas de codificação em alguns clientes ou scripts de automação.

Resumo das ações recomendadas:  
• Mover todos os segredos para Kubernetes Secrets.  
• Definir securityContext (pod e container) para rodar não-root e dropar capabilities.  
• Criar ServiceAccount específico e atribuir RBAC mínimo.  
• Corrigir selector do Service para `app: orionld`.  
• Fixar tags de imagem e usar TLS/Ingress.  
• Adicionar NetworkPolicy, affinity rules e revisar probes/HPA conforme versão do cluster.

## Fix
✅ **Executado apply_manifest:**

```json
🚀 **Aplicado:** {'status': 'success', 'message': 'Sucesso:\ndeployment.apps/fiware-orionld configured\nservice/fiware-orionld-service configured\nhorizontalpodautoscaler.autoscaling/fiware-orionld-hpa unchanged\n'}
```

## K8s
```
NAME                              READY   STATUS              RESTARTS     AGE
fiware-orionld-548584cdf-9vh4t    0/1     Running             1 (7s ago)   32s
fiware-orionld-548584cdf-mpbsr    0/1     Running             1 (7s ago)   32s
fiware-orionld-548584cdf-vqmc9    0/1     Running             1 (7s ago)   32s
fiware-orionld-57c7b45f88-mnzw9   0/1     ContainerCreating   0            0s
```