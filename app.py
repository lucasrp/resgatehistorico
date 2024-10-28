from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route('/', methods=['POST'])
def processar_historico():
    data = request.get_json()

    numero_telefone = data.get('numero_telefone')
    instancia = data.get('instancia')

    if not numero_telefone:
        return jsonify({'error': 'Número de telefone não fornecido'}), 400
    if not instancia:
        return jsonify({'error': 'Nome da instância não fornecido'}), 400

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

        # Retorna a resposta da API Evolution exatamente como está
        return jsonify(data), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f"Erro ao acessar a Evolution API: {e}"}), 500

if __name__ == '__main__':
    app.run()
