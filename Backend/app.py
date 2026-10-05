"""API simples para consultar o modelo Prophet treinado de BTC-USD."""

# Importa as ferramentas de datas, arquivos, tabelas e atendimento HTTP.
from datetime import date, timedelta
from math import isfinite
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, HTTPException
from prophet.serialize import model_from_json
from pydantic import BaseModel, ConfigDict

# Lê o JSON uma única vez quando o servidor inicia.
caminho_modelo = Path(__file__).resolve().parent.parent / "artefatos" / "modelo_prophet.json"
modelo = model_from_json(caminho_modelo.read_text(encoding="utf-8"))
if modelo.history is None or modelo.history.empty or not modelo.params:
    raise RuntimeError("O artefato precisa conter um modelo Prophet treinado.")

# Guarda o fim do treino e desativa intervalos aleatórios que a API não retorna.
ultima_data_treino = modelo.history["ds"].max().date()
modelo.uncertainty_samples = 0
app = FastAPI(title="Previsão de BTC-USD com Prophet")


# A data é opcional; campos extras não pertencem ao pedido de previsão.
class Pedido(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: date | None = None


# Esta rota confirma que o servidor iniciou com o modelo carregado.
@app.get("/health")
def health():
    return {"status": "ok", "modelo": "Prophet", "ultima_data_treino": ultima_data_treino.isoformat()}


# Esta rota recebe uma data e retorna o fechamento previsto em dólares.
@app.post("/predict")
def predict(pedido: Pedido):
    data_previsao = pedido.data or ultima_data_treino + timedelta(days=1)
    if data_previsao <= ultima_data_treino:
        raise HTTPException(status_code=422, detail=f"A data deve ser posterior a {ultima_data_treino}.")

    # Converte a data para a precisão exigida pelo Prophet e rejeita limites inválidos.
    try:
        futuro = pd.DataFrame({"ds": [pd.Timestamp(data_previsao).as_unit("ns")]})
    except (OverflowError, ValueError):
        raise HTTPException(status_code=422, detail="A data está fora do intervalo suportado pelo Prophet.")

    # Passa somente a data ao modelo e extrai sua estimativa central, chamada yhat.
    previsao = modelo.predict(futuro)
    valor = float(previsao["yhat"].iloc[0])
    if not isfinite(valor):
        raise HTTPException(status_code=500, detail="O modelo retornou uma previsão não finita.")

    # Devolve a data solicitada, a estimativa e o corte do treinamento em JSON.
    return {
        "data": data_previsao.isoformat(),
        "valor_previsto": round(valor, 2),
        "moeda": "USD",
        "modelo": "Prophet",
        "ultima_data_treino": ultima_data_treino.isoformat(),
    }
