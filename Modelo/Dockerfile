# Começa com uma imagem que já tem Python instalado.
FROM python:3.12-slim

# Usa /app como pasta de trabalho dentro do container.
WORKDIR /app

# Copia a lista de bibliotecas antes de instalar.
COPY requirements.txt .

# Instala as bibliotecas; dá mais tempo para baixar pacotes grandes.
RUN pip install --timeout 120 -r requirements.txt

# Coloca o programa na imagem; o CSV será criado pelo treino.
COPY treino.py ./

# Executa o treino e mostra as mensagens sem esperar o buffer do Python.
CMD ["python", "-u", "treino.py"]
