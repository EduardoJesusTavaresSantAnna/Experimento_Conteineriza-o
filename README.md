# Bitcoin com Prophet e Docker

Aplicação que treina um modelo Prophet com dados do Bitcoin e disponibiliza
uma API para consultar o preço de fechamento previsto em dólares.

## Requisitos

- Docker instalado e em execução, com Docker Compose.
- Bash e curl para executar o script de teste.
- Internet para baixar imagens, bibliotecas e dados do Yahoo Finance.

## 1. Iniciar a aplicação

Abra o terminal na pasta do projeto, onde está o `compose.yaml`, e execute:

```bash
docker compose up --build -d
```

Aguarde o comando terminar. Ele monta as imagens, executa o treinamento e
inicia o backend depois que o modelo é salvo. A primeira execução pode levar
alguns minutos por causa dos downloads e do treino.

O fluxo é: **coleta de dados → treinamento → modelo salvo → API disponível**.
Os dados, o modelo e os resultados são gerados automaticamente.

## 2. Testar e pedir uma previsão

```bash
bash Cliente/testar_api.sh
```

O script verifica a API e solicita uma previsão. A resposta mostra a data e
o valor previsto em dólares. Como o pedido não informa uma data, a previsão
é para o dia seguinte ao último dia usado no treino.

Para fazer consultas pelo navegador, abra a
[documentação da API](http://127.0.0.1:8000/docs).

## 3. Conferir o funcionamento

```bash
docker compose ps --all
docker compose logs --tail=50
```

O `treino` deve aparecer como `Exited (0)`, indicando que terminou sem erro.
O `backend` deve continuar em execução (`Up`). Se o teste falhar enquanto a
API inicia, aguarde um pouco e execute o script novamente. Os logs mostram
as mensagens dos dois serviços.

## 4. Encerrar a aplicação

```bash
docker compose down
```

O CSV, os resultados e o modelo permanecem nas pastas `Modelo` e `artefatos`.

## Documentação

- [Devlog](DevLog/devlog.md)
- [Diagrama da solução](<Diagrama UML/diagrama_uml.md>)
