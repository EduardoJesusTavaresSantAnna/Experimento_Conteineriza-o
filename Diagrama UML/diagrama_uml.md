# Explicação do diagrama UML — treinamento e inferência

> Registro de planejamento: as escolhas abaixo descrevem a arquitetura proposta, não resultados de execução já comprovados.

## 1. Objetivo da organização

A arquitetura separa **treinar o modelo** de **usar o modelo para prever**. O primeiro container prepara os dados, treina e salva um arquivo. O segundo carrega esse arquivo e atende às solicitações do cliente. Essa divisão atende à proposta da atividade e permite testar cada etapa separadamente.

## 2. Escolhas e justificativas

| Escolha | Função no diagrama e justificativa |
| --- | --- |
| **Yahoo Finance e yfinance** | O Yahoo Finance é a fonte externa. A biblioteca `yfinance` é chamada pelo `treino.py` para obter os dados sem baixar um CSV manualmente. Ela não é outro serviço ou container; é uma dependência do programa. A consulta permite selecionar ativo, período e frequência diária.[^yfinance] |
| **Coleta e treinamento no mesmo treino.py** | Reunir as etapas simplifica a primeira implementação. Mesmo no mesmo arquivo, coleta, preparação, treinamento e exportação devem ter responsabilidades identificáveis. |
| **Validação e EDA** | A etapa proposta verifica datas, tipos, registros duplicados, valores ausentes e comportamento dos preços antes da modelagem. EDA significa análise exploratória dos dados; não é uma garantia de qualidade da previsão. |
| **bitcoin.csv** | Guarda os dados preparados para inspeção e repetição dos testes. No diagrama, ele é salvo e depois lido pelo treinamento. Essa releitura é uma escolha de organização, não uma obrigação: o código também pode continuar usando a tabela em memória. |
| **Separação cronológica** | Os registros antigos ficam no treino e os posteriores no teste, sem embaralhamento. A avaliação procura representar a situação de prever observações futuras com informações anteriores.[^temporal] |
| **Treinamento e avaliação** | O treinamento ajusta o modelo; a avaliação compara suas previsões com os valores reais reservados para teste. Transformações que aprendem parâmetros dos dados devem ser ajustadas apenas no treino, evitando vazamento de informação do teste.[^vazamento] |
| **Arquivo do modelo treinado** | A exportação preserva o modelo para carregá-lo depois, sem repetir o treinamento. O formato será escolhido conforme a biblioteca de modelagem. Esse arquivo não é o CSV nem o código Python.[^persistencia] |
| **Backend Python em outro container** | Na proposta, carrega o artefato ao iniciar e mantém o modelo na memória para atender às requisições. A inferência acontece dentro desse container, sem executar novamente o treinamento. |
| **curl como cliente** | Envia requisições HTTP e apresenta a resposta no terminal. Foi escolhido para demonstrar a comunicação sem construir uma tela. É um cliente de linha de comando, não uma interface gráfica.[^curl] |
| **GET /health e POST /predict** | São as rotas propostas: a primeira consulta o estado do serviço; a segunda solicita uma previsão. O backend deverá validar a entrada e devolver um JSON com o resultado. As rotas separam o teste de disponibilidade do teste de inferência. |

## 3. Por que usar bind mount e mostrar o artefato fora dos containers?

O **bind mount** disponibiliza uma pasta do computador que executa o Docker dentro de um container. A proposta monta a mesma pasta `./artefatos` nos dois containers: o treinamento escreve nela e o backend acessa em **somente leitura**.[^docker]

A escolha facilita inspecionar e compartilhar o arquivo, sem transferência manual, e preserva os dados quando o container é removido. Não é uma cópia automática entre containers: ambos acessam o mesmo armazenamento. A limitação é depender dos caminhos e das permissões dessa máquina.[^docker]

O bloco externo representa **onde o arquivo fica armazenado**, não um terceiro serviço. Depois da leitura, o modelo é executado na memória do backend. Portanto, o nome mais claro para esse bloco é **“Arquivo do modelo — pasta compartilhada”**.

## 4. Sequência prevista no diagrama

**Treinamento:** iniciar o primeiro container → consultar os dados → validar e explorar → preparar e salvar o CSV → ler os dados → separar treino e teste → treinar → avaliar → salvar o modelo na pasta compartilhada.

**Inicialização da inferência:** concluir a gravação do artefato → iniciar o backend → ler o arquivo → carregar o modelo. O container de treinamento pode encerrar; não precisa permanecer ativo para responder às previsões.

**Uso pelo cliente:** executar `curl` → consultar `/health` → solicitar uma previsão em `/predict` → validar os parâmetros → executar a inferência → devolver o resultado em JSON.

Para o cliente no computador alcançar o backend pela configuração de rede proposta, será necessário publicar a porta do serviço. Isso é separado do bind mount: a porta dá acesso ao serviço; a montagem dá acesso aos arquivos.[^portas]

## 5. Como interpretar os elementos do UML

O diagrama de sequência mostra a ordem das interações de cima para baixo. Os blocos identificam os participantes; as setas representam chamadas e retornos; as barras de ativação indicam períodos de execução. Uma seta do `treino.py` para ele mesmo representa uma operação interna.[^uml]

Os participantes `bitcoin.csv` e “Arquivo do modelo” representam armazenamento. Suas setas de retorno significam conclusão de leitura ou gravação, não respostas de servidores independentes. Da mesma forma, encerrar uma barra de ativação do backend não significa desligar o container: significa concluir aquela execução representada.

## 6. O que ainda precisa ser definido e demonstrado

O diagrama ainda não fixa o algoritmo, o formato de exportação, o período histórico nem os parâmetros da requisição de previsão. A proposta inicial é prever o fechamento do dia seguinte em dólares, mas esse contrato precisa ser confirmado na implementação.

O devlog deverá registrar os comandos realmente executados, a geração e o carregamento do artefato e as respostas dos testes. Um `/health` bem-sucedido, sozinho, não demonstra uma previsão funcionando. As previsões são experimentais, conforme o enunciado da atividade.

## Referências técnicas

[^yfinance]: Documentação oficial de `yfinance.download`: `https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html`.
[^temporal]: Scikit-learn — avaliação de séries temporais: `https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-of-time-series-data`.
[^vazamento]: Scikit-learn — vazamento de dados: `https://scikit-learn.org/stable/common_pitfalls.html#data-leakage`.
[^persistencia]: Scikit-learn — persistência de modelos, como referência conceitual: `https://scikit-learn.org/stable/model_persistence.html`.
[^curl]: Manual oficial do curl: `https://curl.se/docs/manpage.html`.
[^docker]: Docker Docs — bind mounts e acesso somente leitura: `https://docs.docker.com/engine/storage/bind-mounts/`.
[^portas]: Docker Docs — publicação de portas: `https://docs.docker.com/get-started/docker-concepts/running-containers/publishing-ports/`.
[^uml]: Mermaid — diagramas de sequência: `https://mermaid.js.org/syntax/sequenceDiagram.html`.