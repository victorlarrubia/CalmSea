import csv
import os
from datetime import datetime

class TCCMetricsCollector:
    def __init__(self, filename="results/benchmark_master.csv"):
        self.filename = filename
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "provider", "model", "duration", "tokens", "prompt_preview"])

    def record(self, provider, model, duration, tokens, prompt):
        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                provider, model, round(duration, 4), tokens, prompt[:50]
            ])