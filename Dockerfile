FROM python:3.10-slim

# Variáveis para otimizar Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalação
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Porta do Streamlit e Porta do CRM HTML
EXPOSE 8501
EXPOSE 8000

# Roda o servidor Python na raiz e o Streamlit em paralelo
CMD ["sh", "-c", "python -m http.server 8000 --bind 0.0.0.0 & streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.baseUrlPath=/prospect --server.fileWatcherType=none --browser.gatherUsageStats=false"]