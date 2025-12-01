import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta, datetime
import requests
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# ================================================
# FUNÇÕES DO SEU MODELO (SEM ALTERAR O CÁLCULO)
# ================================================
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
    return modelo.predict(entrada)[0]

def tendencia_multi_rf(valores, chuva, vento, umidade):
    pred_next = prever_valor(valores, chuva, vento, umidade)
    atual = valores[-1]
    return (pred_next - atual) * 0.8


# ================================================
# FUNÇÃO PRINCIPAL PARA RODAR A PREVISÃO
# ================================================
def calcular_previsao(dia_selecionado):
    latitude = -10.96
    longitude = -37.05

    hoje = date.today()
    last_week = hoje - timedelta(days=7)

    # 🔧 Corrigido: Combobox usa formato dd/mm/YYYY
    dia = datetime.strptime(dia_selecionado, "%d/%m/%Y").date()

    # Vamos usar dados até o dia anterior
    tempo_escolhido = dia - timedelta(days=1)

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}"
        f"&start_date={last_week}&end_date={tempo_escolhido}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        f"wind_speed_10m_max,relative_humidity_2m_mean"
        f"&timezone=America/Sao_Paulo"
    )

    data = requests.get(url).json()

    temps_max = data["daily"]["temperature_2m_max"]
    temps_min = data["daily"]["temperature_2m_min"]
    chuva = data["daily"]["precipitation_sum"]
    vento = data["daily"]["wind_speed_10m_max"]
    umidade = data["daily"]["relative_humidity_2m_mean"]

    media_max = np.mean(temps_max)
    media_min = np.mean(temps_min)

    estacao = estacao_do_ano(hoje)
    media_estacao = climatologia[estacao]
    peso_semana, peso_clima = pesos_estacao[estacao]

    prev_vento = prever_valor(vento, chuva, vento, umidade)
    prev_umidade = prever_valor(umidade, chuva, vento, umidade)
    prev_chuva = prever_valor(chuva, chuva, vento, umidade)

    tend_max = tendencia_multi_rf(temps_max, chuva, vento, umidade)
    tend_min = tendencia_multi_rf(temps_min, chuva, vento, umidade)

    prev_max = (media_max * peso_semana) + (media_estacao * peso_clima) + tend_max
    prev_min = (media_min * peso_semana) + (media_estacao * peso_clima) + tend_min

    return {
        "estacao": estacao.capitalize(),
        "max": prev_max,
        "min": prev_min,
        "vento": prev_vento,
        "umidade": prev_umidade,
        "chuva": prev_chuva,
    }


# ================================================
# INTERFACE GRÁFICA (TKINTER)
# ================================================
def mostrar_previsao():
    dia = combo.get()
    if not dia:
        resultado["text"] = "Selecione um dia!"
        return

    previsao = calcular_previsao(dia)

    texto = (
        f"📅 Dia selecionado: {dia}\n"
        f"🌱 Estação: {previsao['estacao']}\n\n"
        f"🌡 Máxima: {previsao['max']:.1f} °C\n"
        f"🌡 Mínima: {previsao['min']:.1f} °C\n"
        f"💨 Vento: {previsao['vento']:.1f} km/h\n"
        f"💧 Umidade: {previsao['umidade']:.1f} %\n"
        f"🌧 Precipitação: {previsao['chuva']:.1f} mm"
    )

    resultado["text"] = texto


root = tk.Tk()
root.title("Previsão do Tempo - Próxima Semana")
root.geometry("400x420")

tk.Label(
    root,
    text="Selecione um dia da próxima semana:",
    font=("Arial", 12)
).pack(pady=10)

# Dias da próxima semana
hoje = date.today()
prox_semana = [(hoje + timedelta(days=i)).strftime("%d/%m/%Y") for i in range(1, 8)]

combo = ttk.Combobox(root, values=prox_semana, font=("Arial", 11))
combo.pack(pady=10)

btn = tk.Button(
    root,
    text="Ver Previsão",
    command=mostrar_previsao,
    font=("Arial", 12),
    bg="#4CAF50",
    fg="white"
)
btn.pack(pady=15)

resultado = tk.Label(root, text="", font=("Arial", 12), justify="left")
resultado.pack(pady=10)

root.mainloop()
