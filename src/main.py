import requests
from datetime import date, timedelta
from sklearn.ensemble import RandomForestRegressor
import numpy as np

latitude = -10.96
longitude = -37.05

hoje = date.today()
last_day = hoje - timedelta(days=1)
last_week = hoje - timedelta(days=7)

# ------------------------------------
# MÉDIAS CLIMATOLÓGICAS
# ------------------------------------
def estacao_do_ano(d):
    ano = d.year
    estacoes = {
        "verao":  (date(ano, 12, 21), date(ano+1, 3, 20)),
        "outono": (date(ano, 3, 21), date(ano, 6, 20)),
        "inverno":(date(ano, 6, 21), date(ano, 9, 22)),
        "primavera":(date(ano, 9, 23), date(ano, 12, 20)),
    }
    for estacao, (inicio, fim) in estacoes.items():
        if inicio <= d <= fim:
            return estacao
    return "verao"

climatologia = {
    "verao": 27.7,
    "outono": 26.7,
    "inverno": 25.2,
    "primavera": 26.8
}

# Pesos originais
pesos_estacao = {
    "verao": (0.70, 0.30),
    "primavera": (0.65, 0.35),
    "outono": (0.55, 0.45),
    "inverno": (0.45, 0.55),
}

# ------------------------------------
# COLETA DE DADOS
# ------------------------------------
url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={latitude}&longitude={longitude}"
    f"&start_date={last_week}&end_date={last_day}"
    f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
    f"&timezone=America/Sao_Paulo"
)

response = requests.get(url)
data = response.json()

temps_max = data["daily"]["temperature_2m_max"]
temps_min = data["daily"]["temperature_2m_min"]

media_max_semana = sum(temps_max) / len(temps_max)
media_min_semana = sum(temps_min) / len(temps_min)

# ------------------------------------
# IA REAL — Random Forest para prever tendência
# ------------------------------------
def tendencia_ia_rf(valores):
    X = np.arange(len(valores)).reshape(-1, 1)
    y = np.array(valores)

    modelo = RandomForestRegressor(
        n_estimators=200,
        max_depth=4,
        random_state=42
    )
    modelo.fit(X, y)

    pred_next = modelo.predict([[len(valores)]])[0]
    atual = valores[-1]

    # suavização igual sua lógica original
    return (pred_next - atual) * 0.8

tend_max = tendencia_ia_rf(temps_max)
tend_min = tendencia_ia_rf(temps_min)

# ------------------------------------
# PREVISÃO FINAL
# ------------------------------------
estacao = estacao_do_ano(hoje)
media_estacao = climatologia[estacao]
peso_semana, peso_clima = pesos_estacao[estacao]

prev_max = (media_max_semana * peso_semana) + (media_estacao * peso_clima) + tend_max
prev_min = (media_min_semana * peso_semana) + (media_estacao * peso_clima) + tend_min

print(f"Estação atual: {estacao.capitalize()}")
print(f"Média climatológica da estação: {media_estacao} °C\n")

print("===== PREVISÃO DE AMANHÃ (IA PROFISSIONAL — RandomForest) =====")
print(f"Temperatura máxima prevista: {prev_max:.2f} °C")
print(f"Temperatura mínima prevista: {prev_min:.2f} °C")