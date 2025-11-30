import requests
from datetime import date, timedelta

latitude = -10.96
longitude = -37.05
datas = []
hoje = date.today()
last_day = hoje - timedelta(days=1)
last_week = hoje - timedelta(days=8)

url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={latitude}&longitude={longitude}"
    f"&start_date={last_week}&end_date={last_day}"
    f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
    f"&timezone=America/Sao_Paulo"
)

response = requests.get(url)
data = response.json()

datas = data["daily"]["time"]
temp_max = data["daily"]["temperature_2m_max"]
temp_min = data["daily"]["temperature_2m_min"]
precip = data["daily"]["precipitation_sum"]

print("Dados meteorológicos de Aracaju (SE) - Ontem e Hoje:\n")
for i in range(len(datas)):
    print(f"Data: {datas[i]}")
    print(f"Temperatura máxima: {temp_max[i]} °C")
    print(f"Temperatura mínima: {temp_min[i]} °C")
    print(f"Precipitação: {precip[i]} mm\n")