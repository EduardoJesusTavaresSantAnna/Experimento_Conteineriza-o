# Começa com a mesma versão de Python usada no treinamento.
FROM python:3.12-slim

# Usa /app como pasta de trabalho dentro do container.
WORKDIR /app

# Copia a lista de bibliotecas antes de instalar.
COPY requirements.txt .

# Instala as bibliotecas usadas pela API e pelo Prophet.
RUN pip install --timeout 120 -r requirements.txt

# Copia o programa; o modelo chega pela pasta compartilhada.
COPY app.py .

# Inicia o servidor na porta 8000 e aceita a conexão encaminhada pelo Docker.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
