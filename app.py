from flask import Flask, request, jsonify
from utils import buscar_ultima_analise, buscar_historico_conversas

app = Flask(__name__)

@app.route('/analise', methods=['GET'])
def get_analise():
    numero_telefone = request.args.get('numero_telefone')
    instancia = request.args.get('instancia')
    robo = request.args.get('robo')
    analise = buscar_ultima_analise(numero_telefone, instancia, robo)
    return jsonify(analise)

@app.route('/historico', methods=['POST'])
def get_historico():
    numero_telefone = request.json.get('numero_telefone')
    instancia = request.json.get('instancia')
    page = request.json.get('page')
    historico = buscar_historico_conversas(numero_telefone, instancia, page)
    return jsonify(historico)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)