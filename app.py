from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['POST'])
def processar_historico():
    data = request.get_json()
    numero_telefone = data.get('numero_telefone')
    if not numero_telefone:
        return jsonify({'error': 'Número de telefone não fornecido'}), 400

    # Configurações do endpoint original
    url = 'https://evolutionapi.sevenmeet.com/chat/findMessages/Imob%20PB'
    headers = {
        'Content-Type': 'application/json',
        'apikey': os.environ.get('API_KEY')  # A API key será definida no Heroku
    }
    payload = {
        "where": {
            "key": {
                "remoteJid": numero_telefone
            }
        }
    }

    try:
        # Faz a requisição ao endpoint original
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        # Processa e simplifica os dados
        simplified_messages = []
        messages = data.get('messages', {}).get('records', [])
        for msg in messages:
            simplified_msg = {}

            # Extrai 'fromMe'
            simplified_msg['fromMe'] = msg.get('key', {}).get('fromMe', False)

            # Extrai 'mensagem'
            message_content = msg.get('message', {})
            if 'conversation' in message_content:
                simplified_msg['mensagem'] = message_content['conversation']
            elif 'extendedTextMessage' in message_content:
                simplified_msg['mensagem'] = message_content['extendedTextMessage'].get('text', '')
            else:
                simplified_msg['mensagem'] = ''

            # Extrai e formata 'dia' (dia/mês/ano)
            timestamp = msg.get('messageTimestamp', '')
            if timestamp:
                timestamp = int(timestamp)
                date = datetime.fromtimestamp(timestamp)
                simplified_msg['dia'] = date.strftime('%d/%m/%Y')
            else:
                simplified_msg['dia'] = ''

            # Adiciona à lista
            simplified_messages.append(simplified_msg)

        return jsonify(simplified_messages), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Erro ao acessar o endpoint original', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run()