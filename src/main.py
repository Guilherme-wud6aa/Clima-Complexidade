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
    f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
    f"wind_speed_10m_max,relative_humidity_2m_mean"
    f"&timezone=America/Sao_Paulo"
)

response = requests.get(url)
data = response.json()

temps_max = data["daily"]["temperature_2m_max"]
temps_min = data["daily"]["temperature_2m_min"]
chuva = data["daily"]["precipitation_sum"]
vento = data["daily"]["wind_speed_10m_max"]
umidade = data["daily"]["relative_humidity_2m_mean"]

media_max_semana = np.mean(temps_max)
media_min_semana = np.mean(temps_min)

# ------------------------------------
# IA REAL — função genérica para prever qualquer variável
# ------------------------------------
def prever_valor(valores, chuva, vento, umidade):
    X = np.column_stack([
        np.arange(len(valores)),
        chuva,
        vento,
        umidade,
    ])
    y = np.array(valores)

    modelo = RandomForestRegressor(
        n_estimators=250,
        max_depth=6,
        random_state=42
    )
    modelo.fit(X, y)

    entrada = np.array([[len(valores), chuva[-1], vento[-1], umidade[-1]]])
    pred = modelo.predict(entrada)[0]

    return pred

# Previsões individuais
prev_vento = prever_valor(vento, chuva, vento, umidade)
prev_umidade = prever_valor(umidade, chuva, vento, umidade)
prev_chuva = prever_valor(chuva, chuva, vento, umidade)

# Tendências de temperatura usando o mesmo método
def tendencia_multi_rf(valores, chuva, vento, umidade):
    pred_next = prever_valor(valores, chuva, vento, umidade)
    atual = valores[-1]
    return (pred_next - atual) * 0.8

tend_max = tendencia_multi_rf(temps_max, chuva, vento, umidade)
tend_min = tendencia_multi_rf(temps_min, chuva, vento, umidade)

# ------------------------------------
# PREVISÃO FINAL — TEMP
# ------------------------------------
estacao = estacao_do_ano(hoje)
media_estacao = climatologia[estacao]
peso_semana, peso_clima = pesos_estacao[estacao]

prev_max = (media_max_semana * peso_semana) + (media_estacao * peso_clima) + tend_max
prev_min = (media_min_semana * peso_semana) + (media_estacao * peso_clima) + tend_min

# ------------------------------------
# PRINT FINAL
# ------------------------------------
print(f"Estação atual: {estacao.capitalize()}")
print(f"Média climatológica da estação: {media_estacao} °C\n")

print("===== PREVISÃO DE AMANHÃ (IA MULTIVARIÁVEL — RF) =====")
print(f"Temperatura máxima: {prev_max:.1f} °C")
print(f"Temperatura mínima: {prev_min:.1f} °C")
print(f"Vento máximo: {prev_vento:.1f} km/h")
print(f"Umidade média: {prev_umidade:.1f} %")
print(f"Precipitação: {prev_chuva:.1f} mm")