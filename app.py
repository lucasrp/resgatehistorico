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

        # Função para buscar mensagens com verificação de erro
        def buscar_mensagens_com_verificacao(instancia, numero_telefone, limite_paginas):
            mensagens = buscar_mensagens(instancia, numero_telefone, limite_paginas=limite_paginas)
            if isinstance(mensagens, dict) and 'error' in mensagens:
                return mensagens  # Retorna erro se houver falha na Evolution API
            
            if not mensagens:  # Verifica se mensagens estão vazias ou faltando
                return {'error': 'Nenhuma mensagem encontrada na resposta da Evolution API'}
            
            return mensagens

        if ultima_data_analise:
            novas_mensagens = []
            mensagens = buscar_mensagens_com_verificacao(instancia, numero_telefone, limite_paginas=limite_paginas)
            
            if isinstance(mensagens, dict) and 'error' in mensagens:
                return jsonify(mensagens), 500  # Retorna erro detalhado

            for msg in mensagens:
                timestamp = int(msg.get('messageTimestamp', ''))
                msg_date = datetime.fromtimestamp(timestamp)
                if msg_date > ultima_data_analise:
                    novas_mensagens.append(msg)

            todas_mensagens = ultima_analise['dados']['mensagens'] + novas_mensagens
        else:
            todas_mensagens = buscar_mensagens_com_verificacao(instancia, numero_telefone, limite_paginas=limite_paginas)
            
            if isinstance(todas_mensagens, dict) and 'error' in todas_mensagens:
                return jsonify(todas_mensagens), 500  # Retorna erro detalhado

        # Processa e simplifica as mensagens com verificações de conteúdo
        simplified_messages = []
        for msg in todas_mensagens:
            # Verifica os tipos de mensagem para capturar o conteúdo correto
            message_content = ""
            if 'conversation' in msg.get('message', {}):
                message_content = msg['message']['conversation']
            elif 'extendedTextMessage' in msg.get('message', {}):
                message_content = msg['message']['extendedTextMessage'].get('text', '')
            elif 'imageMessage' in msg.get('message', {}):
                message_content = "[Imagem]"  # Opcional: indique tipo de mídia
            elif 'videoMessage' in msg.get('message', {}):
                message_content = "[Vídeo]"  # Opcional: indique tipo de mídia
            # Adicione outros tipos de mensagem conforme necessário

            simplified_msg = {
                'fromMe': msg.get('key', {}).get('fromMe', False),
                'mensagem': message_content,
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
