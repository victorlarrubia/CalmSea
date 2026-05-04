import csv
import os
from datetime import datetime

class TCCMetricsCollector:
    def __init__(self, filename="results/benchmark_master.csv"):
        self.filename = filename
        # Agora usamos uma lista para acumular todas as iterações de um mesmo cenário
        self.temp_interactions = [] 
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Adicionamos 'iterations' para o seu dataset de TCC ficar mais rico
                writer.writerow([
                    "timestamp", "provider", "model", "total_duration", 
                    "total_tokens", "iterations", "gpu_status", "veredito", "history_log"
                ])

    def record(self, provider, model, duration, tokens, prompt, response, gpu_status):
        """O Decorator chama isso a cada 'pensamento' da IA."""
        self.temp_interactions.append({
            "provider": provider, 
            "model": model, 
            "duration": duration,
            "tokens": tokens, 
            "gpu": gpu_status,
            "log": f"Prompt: {prompt[:100]}... | Resposta: {response}"
        })

    def commit(self, is_ok, health_msg):
        """A Main chama isso ao fim do cenário. Consolidamos tudo em uma linha."""
        if not self.temp_interactions:
            return

        # Agregação estatística para o TCC
        total_duration = sum(i["duration"] for i in self.temp_interactions)
        total_tokens = sum(i["tokens"] for i in self.temp_interactions)
        num_iterations = len(self.temp_interactions)
        
        # Pegamos os dados fixos da primeira interação
        base = self.temp_interactions[0]
        status = "SUCCESS" if is_ok else f"FAILED ({health_msg})"
        
        # Concatenamos todo o raciocínio para auditoria qualitativa
        full_history = " || ".join([i["log"] for i in self.temp_interactions])

        with open(self.filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                base["provider"],
                base["model"],
                round(total_duration, 4),
                total_tokens,
                num_iterations,
                base["gpu"],
                status,
                full_history 
            ])
            
        # Limpa o buffer para o próximo cenário
        self.temp_interactions = []