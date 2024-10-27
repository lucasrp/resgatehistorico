from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['POST'])
def processar_historico():
    data = request.get_json()
    
    # Extrair o número de telefone e instância
    numero_telefone = data.get('numero_telefone')
    instancia = data.get('instancia')
    
    # Verificar a presença de `page` explicitamente
    page = data.get('page')  # `page` será None se não estiver no JSON

    # Verifica se os parâmetros obrigatórios foram fornecidos
    if not numero_telefone:
        return jsonify({'error': 'Número de telefone não fornecido'}), 400
    if not instancia:
        return jsonify({'error': 'Nome da instância não fornecido'}), 400

    # Configuração da URL do endpoint externo
    url = f'https://evolutionapi.sevenmeet.com/chat/findMessages/{instancia}'
    headers = {
        'Content-Type': 'application/json',
        'apikey': os.environ.get('API_KEY')  # A API key será definida no Heroku
    }
    
    # Montar o payload com ou sem `page`, dependendo de sua presença
    payload = {
        "where": {
            "key": {
                "remoteJid": numero_telefone
            }
        }
    }
    if page is not None:  # Adicionar `page` somente se fornecido
        payload["page"] = page

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
