# Devlog — 

**Data:** 05/10/2062
**Autor(es):** Eduardo Jesus

# 1. Linha de Racíocinio

## 1.1 Diagrama UML
&emsp; Comecei por montar e estrtura o diagrama da solução, tentando exergar como ela funcionaria e para detalhar da melhor maneira, decidi por onde coletar os dados, como serão salvos, onde ficarão armazenados, qual será a etapa seguinte, como ocorrerá no bloco de treino e modelo seguidos, para então comoserão apresentados os resultados.

&emsp; Para auxiliar na montagem de um diagrama mais adequado, eu pedi a AI para detlahar e fui adiconando e retirando o que se tornava alucinação dela e fora do meu planejamento. Com isso A idealização do fluxo do diagrama ficou da seguinte maneira:

![Diagrama-UML](../Diagrama%20UML/Diagrama-UML.svg)

para detalhes pode ser seguir pela documentação, mas a ideia central é:

1. Decidir de onde será coletado os dados, que no meu caso foi pelo Yahoo Finance, pela facilidade de implementar em código e coletar o que era necessário, além de conter tudo que era necessário.

2. Com isso, dentro de treino.py eu deixei a coleta sendo feita pelo código, em seguida o tratamento de armazenar e logo a montagem d eum csv para uso.

3. Após a EDA feita, realiza-se o treino e validação dos resultados dos dados testes.

4. Assim, seguimos para salvar o modelo treinado via bind mount, que serve apenas para salvar numa pasta compartilhada, assim evita necessitar a cópia da pasta de um container para o outro.

5. Depois de confirmar a gravação, o backend faz a requisição e le o artefato do via bind, e retorna o modelo para a pasta e carrega o modelo na memória.

6. O curl utiliza um GET para pegar o JSON com status do serviço e depois usa um POST para solicitar a previsão.

7. Por fim, o back valida o paramêtros da solicitação, e executa a infêrencia com o modelo carregado. Em seguida, é enviado JSON com data e valor previsto.


## 1.2 Desenvolvimento do modelo

&emsp; Desenvolvi um modelo com Prophet para estimar o preço de
fechamento do Bitcoin em dólares. Para isso, preparei a coleta dos dados diários
do Yahoo Finance desde 2020, organizei as datas e removi registros duplicados
ou com valores inválidos. Também incluí uma análise inicial para conferir o
período, os dias ausentes e um resumo dos valores. Os dados são salvos em CSV
e lidos novamente antes do treinamento.

&emsp; A ideia foi usar o histórico de preços para identificar
tendências e padrões ao longo do tempo. Separei os primeiros 80% dos dias para
treinar e os últimos 20% para testar, mantendo a ordem das datas para não usar
informações futuras no treinamento. Comparei as previsões com os preços reais
e com uma referência simples: repetir o último preço conhecido no treino.
Usei MAE, RMSE e MAPE para medir os erros em dólares e em porcentagem.
Nessa avaliação, o Prophet teve mais erro que a referência.

&emsp; Organizei o código em Python em funções para preparar
os dados, treinar o modelo e executar o processo completo. O volume fica no
CSV, mas o treinamento usa apenas a data e o preço de fechamento. O programa
salva as previsões do teste, as métricas e um gráfico de comparação. Depois,
treina outro modelo com todo o histórico e o salva em JSON para a API carregar
e consultar. O Docker executa o treino antes de iniciar a API, e a opção
`--usar-csv` permite repetir o treinamento com os dados já salvos.
 
&emsp; Usei da AI para montar os códigos para polpar tempo, assim todo o fluxo e ideia que mostrei foi usado como parte para apresentar no prompt que gerou os códigos, sendo feito exatamente como foi mencionado e explicado.

 ## 1.3 Conteinerização e integração dos arquivos

Organizei a execução em dois containers: um para treinar o modelo e outro
para atender às consultas pela API. Cada um tem seu próprio `Dockerfile`.
Nos dois, o `FROM` escolhe uma imagem com Python 3.12, o `WORKDIR` define a
pasta de trabalho, o `COPY` copia os arquivos e o `RUN` instala as bibliotecas
listadas no `requirements.txt`. Por último, o `CMD` define o que será executado:
no treino, o programa `treino.py`; no backend, o servidor Uvicorn que atende à API.

Para colocar essas partes juntas, usei o `compose.yaml`. O `build` indica a
pasta de cada Dockerfile, e o `depends_on`, com
`service_completed_successfully`, faz o backend esperar o treinamento terminar
sem erro. Essa ordem é necessária porque a API precisa encontrar o modelo
salvo antes de começar a receber consultas.

Os `volumes` ligam pastas do computador às pastas dos containers. A pasta
`Modelo` guarda o CSV e os resultados, enquanto `artefatos` recebe o modelo
em JSON e fica disponível para os dois serviços. Assim, o treino salva o
arquivo e a API consegue carregá-lo. No backend, o `:ro` permite apenas a
leitura dessa pasta.

Também usei o `.dockerignore` do treino para deixar o CSV, os resultados e os
arquivos temporários fora da montagem da imagem. O `Cliente/testar_api.sh`
roda no computador e usa `curl` para verificar a API e pedir uma previsão.
O fluxo ficou: **Compose prepara os containers → treino coleta os dados e
salva o modelo → API carrega o JSON → cliente consulta a API**.

Como ainda estou entendendo sobre o Docker e não domino todas essas configurações,
usei IA para entender como montar certas partes do código, principalmente os
volumes e a ordem de execução no Compose. Esse apoio me ajudou a relacionar
cada configuração com sua função no projeto e a entender como os arquivos
trabalham juntos.

## 1.4 Desenvolvimento do backend

&emsp; O backend foi montado completamente com IA, incluindo o código da API,
o carregamento do modelo e as verificações das datas. Como ainda não tenho
domínio dessa implementação, precisei desse apoio para construir essa parte.
Por isso, deixo aqui um resumo do funcionamento, seguindo o fluxo apresentado
no diagrama.

&emsp; O código está em `Backend/app.py` e usa FastAPI para receber os pedidos.
Quando a API inicia, ela lê o modelo salvo em JSON na pasta `artefatos` e o
mantém na memória para usar nas consultas. A função do backend é receber uma
data, consultar esse modelo já treinado e devolver a previsão do preço do
Bitcoin em dólares.

&emsp; A rota `GET /health` informa se a API iniciou com o modelo carregado.
A `POST /predict` recebe a data e retorna a previsão em JSON. Se nenhuma data
for informada, o código usa o dia seguinte ao último dia do treino. Também
recusa datas inválidas ou anteriores ou iguais ao último dia usado no
treinamento. Assim, o caminho é: **pedido do cliente → verificação da data →
consulta ao modelo → resposta com a previsão**.

# 2 Conclucão

&emsp; Nessa atividade consegui me aproveitar bem para montar o UML e entender bem sobre os comandos usados no docker e como funciona o `compose.yaml` para conectar os containers e a criação das imagens por meio de documentações externas e auxilio da AI para implementação. Além de conhecer novos métodos de coleta de dados, como foi o caso do yfinance, e com isso acredito que a única coisa que não pude desenvolver bem por conta própria foi meu backend e o cliente em curl, já que não pude, por tempo e conehcimento, colocar de maneira honesta e por minha conta, por isso o entendimento nela não foi por minha parte