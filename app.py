from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

# URL e chave de API do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

# Headers de autenticação para chamadas à API do Supabase
supabase_headers = {
    'apikey': SUPABASE_API_KEY,
    'Authorization': f'Bearer {SUPABASE_API_KEY}',
    'Content-Type': 'application/json'
}

# Função para buscar a última análise pelo número de telefone
def buscar_ultima_analise(numero_telefone):
    url = f"{SUPABASE_URL}/rest/v1/conversasanalises"  # Nome exato da tabela
    params = {
        'select': '*',
        'telefone': f"eq.{numero_telefone}",
        'order': 'momento_analise.desc',
        'limit': '1'
    }
    try:
        response = requests.get(url, headers=supabase_headers, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]  # Retorna o JSON da última análise
        return None
    except requests.exceptions.RequestException as e:
        return {'error': f"Erro ao buscar análise no Supabase: {e}"}

# Função para buscar mensagens do Evolution API
def buscar_mensagens(instancia, numero_telefone, page=None, limite_paginas=1):
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
    if page is not None:
        payload["page"] = page

    mensagens = []
    for i in range(limite_paginas):
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            mensagens.extend(data.get('messages', {}).get('records', []))
            if 'nextPage' not in data:
                break
            payload["page"] = data['nextPage']
        except requests.exceptions.RequestException as e:
            return {'error': f"Erro ao acessar Evolution API: {e}"}
    return mensagens

@app.route('/', methods=['POST'])
def processar_historico():
    try:
        data = request.get_json()

        numero_telefone = data.get('numero_telefone')
        instancia = data.get('instancia')
        limite_paginas = data.get('limite_paginas', 1)

        if not numero_telefone:
            return jsonify({'error': 'Número de telefone não fornecido'}), 400
        if not instancia:
            return jsonify({'error': 'Nome da instância não fornecido'}), 400

        ultima_analise = buscar_ultima_analise(numero_telefone)
        
        if isinstance(ultima_analise, dict) and 'error' in ultima_analise:
            return jsonify(ultima_analise), 500  # Retorna erro se houver falha na busca no Supabase
        
        ultima_data_analise = None
        if ultima_analise:
            ultima_data_analise = datetime.fromisoformat(ultima_analise['momento_analise'])

        if ultima_data_analise:
            novas_mensagens = []
            mensagens = buscar_mensagens(instancia, numero_telefone, limite_paginas=limite_paginas)
            
            if isinstance(mensagens, dict) and 'error' in mensagens:
                return jsonify(mensagens), 500  # Retorna erro se houver falha na Evolution API
            
            for msg in mensagens:
                timestamp = int(msg.get('messageTimestamp', ''))
                msg_date = datetime.fromtimestamp(timestamp)
                if msg_date > ultima_data_analise:
                    novas_mensagens.append(msg)

            todas_mensagens = ultima_analise['dados']['mensagens'] + novas_mensagens
        else:
            todas_mensagens = buscar_mensagens(instancia, numero_telefone, limite_paginas=limite_paginas)
            
            if isinstance(todas_mensagens, dict) and 'error' in todas_mensagens:
                return jsonify(todas_mensagens), 500  # Retorna erro se houver falha na Evolution API

        simplified_messages = []
        for msg in todas_mensagens:
            simplified_msg = {
                'fromMe': msg.get('key', {}).get('fromMe', False),
                'mensagem': msg.get('message', {}).get('extendedTextMessage', {}).get('text', ''),
                'dia': datetime.fromtimestamp(int(msg.get('messageTimestamp', ''))).strftime('%d/%m/%Y'),
                'hora': datetime.fromtimestamp(int(msg.get('messageTimestamp', ''))).strftime('%H:%M:%S')
            }
            simplified_messages.append(simplified_msg)

        dados_para_analise = {
            "numero_telefone": numero_telefone,
            "momento_analise": datetime.now().isoformat(),
            "mensagens": simplified_messages
        }

        return jsonify(dados_para_analise), 200

    except Exception as e:
        return jsonify({'error': f"Erro interno do servidor: {e}"}), 500

if __name__ == '__main__':
    app.run()
