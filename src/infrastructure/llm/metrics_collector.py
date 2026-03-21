import csv
import time
import os

class TCCMetricsCollector:
    def __init__(self, filename="logs/benchmark_results.csv"):
        self.filename = filename
        os.makedirs("logs", exist_ok=True)
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "provider", "model", "duration", "tokens", "prompt"])

    def record(self, provider, model, duration, tokens, prompt):
        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                provider,
                model,
                round(duration, 4),
                tokens,
                prompt[:50].replace("\n", " ") # Limpa o prompt para o CSV
            ])