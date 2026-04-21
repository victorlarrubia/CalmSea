import csv
import os
from datetime import datetime

class TCCMetricsCollector:
    def __init__(self, filename="results/benchmark_master.csv"):
        self.filename = filename
        
        # Garante que a pasta results exista antes de tentar criar o arquivo
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Cabeçalho atualizado com os novos requisitos
                writer.writerow([
                    "timestamp", "provider", "model", "duration", 
                    "tokens", "gpu_status", "prompt", "response"
                ])

    def record(self, provider, model, duration, tokens, prompt, response, gpu_status):
        with open(self.filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                provider, 
                model, 
                round(duration, 4), 
                tokens,
                gpu_status,
                prompt,
                str(response) # str() garante que tool calls não quebrem o CSV
            ])