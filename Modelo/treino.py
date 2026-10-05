"""Coleta Bitcoin, avalia Prophet e salva um modelo para o backend."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Salva gráficos mesmo dentro de um container sem tela.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from prophet import Prophet, __version__ as VERSAO_PROPHET
from prophet.serialize import model_to_json

# Os caminhos funcionam no projeto e nos volumes definidos pelo Docker Compose.
PASTA = Path(__file__).resolve().parent
CSV = PASTA / "bitcoin.csv"
RESULTADOS = PASTA / "resultados"
ARTEFATOS = PASTA.parent / "artefatos"


def preparar_dados(dados):
    """Remove registros inválidos e deixa os dias em ordem."""
    if not {"Close", "Volume"}.issubset(dados.columns):
        raise ValueError("Os dados precisam conter Close e Volume.")
    dados = dados[["Close", "Volume"]].copy()
    dados.index = pd.to_datetime(dados.index, errors="coerce", utc=True).tz_convert(None).normalize()
    for coluna in dados.columns:
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")  # Converte textos numéricos para números.
    dados = dados.replace([np.inf, -np.inf], np.nan).dropna()
    dados = dados[(dados["Close"] > 0) & (dados["Volume"] >= 0)]
    dados = dados[dados.index.notna()]
    dados = dados[~dados.index.duplicated(keep="last")].sort_index()
    dados.index.name = "Date"
    if len(dados) < 10:
        raise ValueError("São necessários pelo menos 10 dias válidos para treinar e testar.")
    return dados


def treinar_modelo(dados):
    """Cria um novo Prophet e aprende somente com os dias recebidos."""
    modelo = Prophet(daily_seasonality=False, interval_width=0.8)
    modelo.fit(dados[["ds", "y"]], seed=42)
    return modelo


def main():
    if sys.argv[1:] not in ([], ["--usar-csv"]):
        raise ValueError("Use: python treino.py [--usar-csv]")

    # Busca dias completos no Yahoo; a opção permite repetir o treino sem internet.
    if "--usar-csv" in sys.argv:
        dados = pd.read_csv(CSV, index_col="Date")
    else:
        dados = yf.download("BTC-USD", start="2020-01-01",
                            end=datetime.now(timezone.utc).date().isoformat(), interval="1d",
                            auto_adjust=False, multi_level_index=False, progress=False, timeout=30)
        if dados is None or dados.empty:
            raise ValueError("O Yahoo não retornou dados. Tente novamente ou use --usar-csv.")
    dados = preparar_dados(dados)

    # A EDA mostra o período, lacunas e estatísticas; depois gravamos e relemos o CSV.
    print(f"Dados: {len(dados)} dias, de {dados.index.min().date()} a {dados.index.max().date()}")
    calendario = pd.date_range(dados.index.min(), dados.index.max(), freq="D")
    print(f"Dias ausentes: {len(calendario.difference(dados.index))}")
    print(dados.describe().round(2))
    CSV.parent.mkdir(parents=True, exist_ok=True)
    dados.to_csv(CSV, index_label="Date", date_format="%Y-%m-%d")
    print(f"CSV salvo: {CSV}")
    dados = preparar_dados(pd.read_csv(CSV, index_col="Date"))
    dados = dados.reset_index().rename(columns={"Date": "ds", "Close": "y"})[["ds", "y"]]

    # Os 80% mais antigos treinam; os 20% mais recentes ficam fora do ajuste.
    corte = int(len(dados) * 0.8)
    treino, teste = dados.iloc[:corte].copy(), dados.iloc[corte:].copy()
    modelo = treinar_modelo(treino)
    np.random.seed(42)  # Repete a simulação dos intervalos da avaliação.
    previstos = modelo.predict(teste[["ds"]]).set_index("ds")  # Fornece só datas, sem preços do teste.
    previsoes = teste.set_index("ds").join(previstos[["yhat", "yhat_lower", "yhat_upper"]])
    if not np.isfinite(previsoes[["yhat", "yhat_lower", "yhat_upper"]].to_numpy()).all():
        raise ValueError("O Prophet retornou previsões inválidas.")
    previsoes = previsoes.rename(columns={"y": "Real_Close", "yhat": "Predicted_Close",
                                         "yhat_lower": "Lower_80", "yhat_upper": "Upper_80"})
    previsoes.index.name = "Date"
    previsoes["Baseline_Close"] = float(treino["y"].iloc[-1])  # Referência: repetir o último preço conhecido.
    previsoes["Horizon_Days"] = (previsoes.index - treino["ds"].iloc[-1]).days

    # Compara Prophet e referência usando exatamente os mesmos preços reais.
    metricas = {}
    for nome, coluna in [("modelo", "Predicted_Close"), ("baseline", "Baseline_Close")]:
        erros = previsoes["Real_Close"] - previsoes[coluna]
        metricas[nome] = {"mae_usd": float(np.abs(erros).mean()),
                         "rmse_usd": float(np.sqrt((erros ** 2).mean())),
                         "mape_pct": float((np.abs(erros / previsoes["Real_Close"])).mean() * 100)}
    relatorio = {"ativo": "BTC-USD", "modelo": "Prophet", "fracao_teste": 0.2,
                 "treino": {"registros": len(treino), "inicio": str(treino["ds"].min().date()), "fim": str(treino["ds"].max().date())},
                 "teste": {"registros": len(teste), "inicio": str(teste["ds"].min().date()), "fim": str(teste["ds"].max().date())},
                 "metricas": metricas}
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    previsoes.to_csv(RESULTADOS / "previsoes_teste.csv", date_format="%Y-%m-%d")
    (RESULTADOS / "metricas.json").write_text(json.dumps(relatorio, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    previsoes[["Real_Close", "Predicted_Close", "Baseline_Close"]].plot(figsize=(10, 5), title="BTC-USD: avaliação no teste", ylabel="USD")
    plt.tight_layout()
    plt.savefig(RESULTADOS / "avaliacao.png")
    plt.close()
    print(pd.DataFrame(metricas).T.round(2))
    print("Menor erro é melhor. As métricas acima avaliam somente o primeiro modelo.")

    # Após salvar a avaliação, outro Prophet usa 100% do histórico para a inferência.
    modelo_final = treinar_modelo(dados)
    ARTEFATOS.mkdir(parents=True, exist_ok=True)
    (ARTEFATOS / "modelo_prophet.json").write_text(model_to_json(modelo_final), encoding="utf-8")
    metadados = {"modelo": "Prophet", "prophet_versao": VERSAO_PROPHET,
                 "registros": len(dados), "ultima_data": str(dados["ds"].max().date()),
                 "metricas_validacao": metricas,
                 "observacao": "Modelo final usa 100% dos dados; métricas pertencem ao ajuste anterior de 80%."}
    (ARTEFATOS / "metadata.json").write_text(json.dumps(metadados, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(f"Modelo final salvo: {ARTEFATOS / 'modelo_prophet.json'}")


if __name__ == "__main__":
    main()
