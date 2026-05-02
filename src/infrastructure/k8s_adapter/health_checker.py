import os
import time
import json

class K8sHealthChecker:
    def check_health(self, ns, timeout=120): # Aumentamos o timeout para 120s (importante para CPU)
        start = time.time()
        # Estados que indicam que a "Vontade Técnica" falhou categoricamente
        fail_states = ["CrashLoopBackOff", "Error", "ImagePullBackOff", "ErrImagePull", "CreateContainerConfigError"]
        
        while time.time() - start < timeout:
            # 1. Captura em JSON para precisão cirúrgica
            cmd = f"kubectl get pods -n {ns} -o json"
            try:
                output = os.popen(cmd).read()
                if not output or output.strip() == "":
                    print(f"[*] {ns}: Aguardando criação dos recursos...")
                    time.sleep(5)
                    continue
                
                data = json.loads(output)
                pods = data.get('items', [])
                
                if not pods:
                    time.sleep(5)
                    continue

                all_ready = True
                current_statuses = []

                for pod in pods:
                    pod_name = pod['metadata']['name']
                    status_obj = pod.get('status', {})
                    phase = status_obj.get('phase', 'Unknown')
                    
                    # Verificação profunda nos containers
                    container_statuses = status_obj.get('containerStatuses', [])
                    for cs in container_statuses:
                        state = cs.get('state', {})
                        # Se algum container estiver em estado de erro conhecido
                        waiting_reason = state.get('waiting', {}).get('reason', '')
                        if waiting_reason in fail_states:
                            return False, f"Falha Crítica no Pod {pod_name}: {waiting_reason}"
                        
                        # Se o container não estiver 'ready', o ambiente ainda não é soberano
                        if not cs.get('ready', False):
                            all_ready = False
                    
                    if phase != "Running" and phase != "Succeeded":
                        all_ready = False
                    
                    current_statuses.append(f"{pod_name}:{phase}")

                if all_ready:
                    return True, "Sucesso: Ambiente íntegro e estável"

                print(f"[*] {ns}: Estabilizando pods... ({', '.join(current_statuses)})")

            except Exception as e:
                print(f"[!] Erro no Health Check: {e}")
            
            time.sleep(5) # Intervalo maior para não sobrecarregar a CPU do benchmark

        return False, "Timeout: Os recursos não atingiram estabilidade no tempo previsto"