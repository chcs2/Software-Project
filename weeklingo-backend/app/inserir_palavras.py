import json
import requests
import os

# 1. Configurações
API_URL = "http://127.0.0.1:8000/words/" 

# SE a tua rota /words/ exigir que o utilizador esteja logado, 
# faz login no teu frontend, copia o token do LocalStorage e cola aqui:
TOKEN = "" 

# 2. Ler o ficheiro JSON
with open('palavras.json', 'r', encoding='utf-8') as file:
    palavras = json.load(file)

# 3. Cabeçalhos para o pedido
headers = {
    'Content-Type': 'application/json'
}
if TOKEN:
    headers['Authorization'] = f'Bearer {TOKEN}'

# 4. Inserir palavras com um loop (Sementeira / Seeding)
sucessos = 0
erros = 0

print("A iniciar a inserção de palavras...\n")

for palavra in palavras:
    resposta = requests.post(API_URL, json=palavra, headers=headers)
    
    if resposta.status_code in [200, 201]:
        print(f"✅ Inserida: {palavra['english_word']}")
        sucessos += 1
    else:
        print(f"❌ Erro em '{palavra['english_word']}': {resposta.text}")
        erros += 1

# 5. Relatório final
print(f"\n--- RESUMO ---")
print(f"Sucessos: {sucessos}")
print(f"Erros: {erros}")