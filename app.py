from flask import Flask, request, jsonify, redirect
from flask_pymongo import PyMongo

from werkzeug.security import generate_password_hash, check_password_hash

from bson import json_util

from config import MONGO_URI

app = Flask(__name__)
app.config['MONGO_URI'] = MONGO_URI
app.config['DEBUG'] = True

app_context = app.app_context()
app_context.push()

mongo = PyMongo(app)

col_users = mongo.db.users
col_questions = mongo.db.questions

@app.route('/', methods=['GET'])
def index():
    res = col_users.find({})
    return json_util.dumps(list(res)), 201

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    data['password'] = generate_password_hash(data['password'])
    col_users.insert_one(data)
    return 'usuario ' + data['username'] + ' criado.', 201

@app.route('/users/<username>', methods=['GET'])
def get_user(username):
    return username, 200

# rota para exemplificar como utilizar obter variaveis
# de url. teste acessando 
# http://localhost:8088/questions/search?disciplina=BancoDeDados 
@app.route('/questions/search', methods=['GET'])
def search():
    disciplina = request.args.get('disciplina')
    return disciplina, 200


# Atividades


# Atividades

#Exercício 01
@app.route('/v1/pablo/users/', methods=['PUT'])
def insert_user():
    data = request.get_json()
    res = col_users.find({'username':data['username']})

    if (len(list(res)) > 0):
        return 'Usuário ' + data['username'] + ' já existe!', 203
    else:
        data['password'] = generate_password_hash(data['password'])
        col_users.insert_one(data)
        return 'Usuário ' + data['username'] + ' criado!', 201

#Exercício 02
@app.route('/v1/pablo/users/<username>', methods=['GET'])
def search_user(username):
    res = col_users.find({'username':username})
    
    if (len(list(res)) > 0):
        res = col_users.find({'username':username})
        return json_util.dumps(res), 200
    else:
        return 'Usuário ' + username + ' não existe!', 404

#Exercício 03
@app.route('/v1/pablo/authenticate', methods=['POST'])
def authenticate_user():
    data = request.get_json()
    
    if(data['username'] and  data['password'])
        user = col_users.find({'username':data['username'], 'password':})

        check_password_hash(

            


# Deletar usuarios
@app.route('/v1/delete', methods=['GET'])
def delete_users():
    col_users.remove()
    return 'OK'