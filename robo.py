import requests
import time

print("🤖 Robô Caçador de Rolês Iniciado...")

# Esses são os eventos que o robô "achou" na internet
eventos_raspados = [
    {"title": "Tardezinha do Pagode", "venue": "Clube de Campo", "price": "Portaria", "category": "Live Music", "image": "https://images.unsplash.com/photo-1514525253344-f81bcc353c58?w=500"},
    {"title": "Eletrônica Underground", "venue": "Galpão Abandonado", "price": "Ingresso Antecipado", "category": "Party", "image": "https://images.unsplash.com/photo-1622909589989-746803dfa348?w=500"},
    {"title": "Noite do Karaokê Anos 80", "venue": "Bar Neon", "price": "Entrada Free", "category": "Karaoke", "image": "https://images.unsplash.com/photo-1760598742492-7ad941e658e5?w=500"}
]

# URL da sua API que está ligada no outro terminal
URL_SUA_API = "http://127.0.0.1:8000/roles/sugerir"

print(f"📡 Encontrei {len(eventos_raspados)} eventos. Enviando para análise do Chefe...")

for evento in eventos_raspados:
    parametros = {
        "title": evento["title"],
        "venue": evento["venue"],
        "estado": "SP",
        "cidade": "São Paulo", 
        "price": evento["price"],
        "category": evento["category"],
        "image": evento["image"]
    }
    
    # O robô manda os dados para a API
    resposta = requests.post(URL_SUA_API, params=parametros)
    
    if resposta.status_code == 200:
        print(f"✅ Enviado com sucesso: {evento['title']}")
    else:
        print(f"❌ Erro ao enviar: {evento['title']}")
    
    time.sleep(1) # Espera 1 segundo pra não travar

print("🏁 Trabalho concluído! Chefe, abra seu painel de Admin para aprovar.")