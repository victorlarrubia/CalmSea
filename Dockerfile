# Usa uma imagem Python leve e moderna
FROM python:3.12-slim

# Evita que o Python gere arquivos .pyc e bufferize stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências do sistema (se precisar de curl, git, etc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala o kubectl dentro do container
RUN apt-get update && apt-get install -y curl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Copia e instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte do projeto
COPY src/ src/

# Expõe a porta do Streamlit
EXPOSE 8501

# Comando para iniciar o App
CMD ["streamlit", "run", "src/presentation/streamlit/app.py", "--server.port=8501", "--server.address=0.0.0.0"]