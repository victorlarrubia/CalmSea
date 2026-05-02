import os
import time

class K8sScenarioManager:
    def __init__(self):
        self.ns_map = {
            "1-orion": "teste-orion", "2-frontend": "teste-frontend",
            "3-mysql": "teste-mysql", "4-vllm": "teste-vllm",
            "5-nginx": "teste-nginx", "6-selenium": "teste-selenium",
            "7-elasticsearch": "teste-elasticsearch", "8-newrelic": "teste-newrelic",
            "9-storm": "teste-storm", "10-mongodb": "teste-mongodb", "fiware-minikube" : "teste-fiware-minikube"
        }

    def prepare(self, yaml_file):
        base = yaml_file.replace(".yaml", "")
        ns = self.ns_map.get(base, "default")
        
        # 1. A Antítese: Gatilho de destruição total
        # --force e --grace-period=0 aceleram a remoção de recursos teimosos
        print(f"[*] Iniciando faxina no namespace: {ns}")
        os.system(f"kubectl delete namespace {ns} --ignore-not-found --grace-period=0 --force > /dev/null 2>&1")
        
        # 2. O Zazen da Infra: Loop de espera ativa
        # Verificamos se o namespace ainda existe no domínio do real
        retries = 0
        while os.system(f"kubectl get namespace {ns} > /dev/null 2>&1") == 0:
            if retries > 30: # Timeout de 60 segundos (30 * 2s)
                print(f"[!] Alerta: O namespace {ns} está em 'limbo' (Terminating). Forçando continuidade...")
                break
            time.sleep(2)
            retries += 1
        
        # 3. A Síntese: Reconstrução do território
        print(f"[*] Reconstruindo ambiente para o cenário: {yaml_file}")
        os.system(f"kubectl create namespace {ns} > /dev/null 2>&1")
        
        # Aplica o cenário vulnerável no namespace limpo
        exit_code = os.system(f"kubectl apply -f docs/tests/scenarios/{yaml_file} -n {ns} > /dev/null 2>&1")
        
        if exit_code != 0:
            print(f"[❌] Falha crítica ao aplicar o cenário {yaml_file} no namespace {ns}.")
        else:
            print(f"[✅] Ambiente pronto e isolado: {ns}")
            
        return ns

    def get_live_yaml(self, ns, yaml_path):
        # Correção 1: Introspecção (Puxa o YAML real que está rodando)
        cmd = f"kubectl get -f {yaml_path} -n {ns} -o yaml"
        return os.popen(cmd).read()