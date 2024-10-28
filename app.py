from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# URL e chave de API do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

# Headers para chamadas à API do Supabase
supabase_headers = {
    'apikey': SUPABASE_API_KEY,
    'Authorization': f'Bearer {SUPABASE_API_KEY}',
    'Content-Type': 'application/json'
}

# Função para buscar a última análise pelo número de telefone e instância no Supabase
def buscar_ultima_analise(numero_telefone, instancia):
    url = f"{SUPABASE_URL}/rest/v1/conversasanalises"  # Nome da tabela no Supabase
    params = {
        'select': '*',
        'telefone': f"eq.{numero_telefone}",
        'instancia': f"eq.{instancia}",
        'order': 'momento_analise.desc',
        'limit': '1'
    }
    try:
        response = requests.get(url, headers=supabase_headers, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]  # Retorna a última análise como JSON
        return None
    except requests.exceptions.RequestException as e:
        return {'error': f"Erro ao buscar análise no Supabase: {e}"}

@app.route('/', methods=['POST'])
def processar_historico():
    data = request.get_json()

    numero_telefone = data.get('numero_telefone')
    instancia = data.get('instancia')

    if not numero_telefone:
        return jsonify({'error': 'Número de telefone não fornecido'}), 400
    if not instancia:
        return jsonify({'error': 'Nome da instância não fornecido'}), 400

    # Busca a última análise no Supabase considerando telefone e instância
    ultima_analise = buscar_ultima_analise(numero_telefone, instancia)

    # Configuração da URL e dos headers para a Evolution API
    url = f'https://evolutionapi.sevenmeet.com/chat/findMessages/{instancia}'
    headers = {
        'Content-Type': 'application/json',
        'apikey': os.environ.get('API_KEY')
    }
    payload = {
        "where": {
            "key": {
                "remoteJid": numero_telefone
            }
        }
    }

    try:
        # Faz a requisição para obter a primeira página de mensagens
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        # Adiciona a última análise ao output
        output = {
            'ultima_analise': ultima_analise,
            'mensagens_evolution_api': data
        }

        return jsonify(output), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f"Erro ao acessar a Evolution API: {e}"}), 500

if __name__ == '__main__':
    app.run()

