from flask import Flask, request, jsonify, redirect
from flask_pymongo import PyMongo

from werkzeug.security import generate_password_hash, check_password_hash

from bson import json_util

from config import MONGO_URI
from auth import *


app = Flask(__name__)
app.config['MONGO_URI'] = MONGO_URI
app.config['DEBUG'] = True

app_context = app.app_context()
app_context.push()

mongo = PyMongo(app)

col_users = mongo.db.users
col_questions = mongo.db.questions
col_tokens = mongo.db.tokens        # refresh tokens


def authenticate(username, password):
    user = col_users.find_one({'username': username})
    if user and check_password_hash(user['password'], password):
        return user
    else:
        return None

@app.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    user = authenticate(data['username'], data['password'])
    if user:
        token_payload = {'username': user['username']}
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)
        col_tokens.insert_one({'value': refresh_token})
        return jsonify({'access_token': access_token, 
                        'refresh_token': refresh_token})
    else:
        return "Unauthorized", 401


# rota para visualizar o conteudo do payload encriptado no token.
@app.route('/token', methods=['GET'])
@jwt_required
def token():    
    return json_util.dumps(g.parsed_token), 200

@app.route('/', methods=['GET'])
#@jwt_required
def index():
    res = col_users.find({})
    return json_util.dumps(list(res)), 200

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

@app.route('/refresh_token', methods=['GET'])
@jwt_refresh_required
def refresh_token():    
    token = col_tokens.find_one({'value': g.token})
    if token:
        col_tokens.delete_one({'value': g.token})
        token_payload = {'username': g.parsed_token['username']}
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)
        col_tokens.insert_one({'value': refresh_token})
        return json_util.dumps({'access_token': access_token, 
                                'refresh_token': refresh_token}), 200
    else:
        return "Unauthorized", 401


# Atividades


# Atividades

#Exercício 00
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

#Exercício 01
@app.route('/v1/pablo/users/<username>', methods=['GET'])
def search_user(username):
    res = col_users.find({'username':username})
    
    if (len(list(res)) > 0):
        res = col_users.find({'username':username})
        return json_util.dumps(res), 200
    else:
        return 'Usuário ' + username + ' não existe!', 404

#Exercício 02
@app.route('/v1/pablo/user/authenticate', methods=['POST'])
def authenticate_user():
    data = request.get_json()
    
    if (data['username'] and data['password']):
        user = col_users.find_one({'username':data['username']})

        if (user and check_password_hash(user['password'], data['password'])):
            return 'Usuário Autenticado!', 200
        else:
            return 'Usuário e ou senha incorreta!', 403
    else:
        return 'Favor informar usuário e senha.', 401

#Exercício 03
@app.route('/v1/pablo/user/update', methods=['POST']) 
#@jwt_required
def update_user():
    data = request.get_json()

    if not data['username']:
        return 'Favor informar o nome do usuário.', 401

    usuario = col_users.find_one({'username':data['username']})

    if not usuario:
        return 'Não existe usuário ' + data['username'], 401
    
    if data['name']:
        col_users.update_one({'username':data['username']}, {'$set':{'name': data['name']} })
    if data['email']:
        col_users.update_one({'username':data['username']}, {'$set':{'email': data['email']} })
    if data['phones']:
        col_users.update_one({'username':data['username']}, {'$set':{'phones': data['phones']} })
        
    return 'Usuário atualizado!', 200
    
        


#Exercicio04
@app.route('/v1/pablo/user/updatepassword', methods=['PATCH'])
def update_password_user():
    data = request.get_json()

    if data['username']:
        user = col_users.find_one({'username':data['username']})
        if user:
            hash_password = generate_password_hash(data['password'])
            col_users.update_one({'username':data['username']}, {'$set':{'password': hash_password}})
            return 'Senha atualizada!', 200
        else:
            return 'Não existe usuário ' + data['username'], 403
    else:
        return 'Favor informar usuário.', 401

#Exercicio05
@app.route('/v1/pablo/questions/<question_id>', methods=['GET'])
def get_question(question_id):
    question = col_questions.find_one({'id':question_id})

    if question:
        return json_util.dumps(question), 200
    else:
        return 'Não foi possível encontrar esta questão!', 404


#Exercício06
@app.route('/v1/pablo/questions/<question_id>', methods=['POST'])
@jwt_required
def set_comment_question(question_id):
    data = request.get_json()
    question = col_questions.find_one({'id':question_id})
    user = col_users.find_one({'username':data['username']})

    if question:
        if (user and data['message']):
            
            if 'comments' not in question:
                comment = []
                comment.append(json_util.dumps({'username': data['username'], 'message': data['message']}))
                col_questions.update_one({'id':question_id}, {'$set':{'comments':comment}})
            else:
                comment = json_util.dumps({'username': data['username'], 'message': data['message']})
                col_questions.update_one({'id':question_id}, {'$push':{'comments':comment}})

            question = col_questions.find_one({'id':question_id})
            return json_util.dumps(question), 200

        else:
            return 'Usuário não existe ou os dados informados são inválidos', 401
    else:
        return 'Não foi possível encontrar esta questão!', 404


#Exercicio07
#@app.route('/v1/pablo/questions/search/', methods=['GET'])
#def search_questions():
#   disciplina = request.args.get('disciplina')
#    ano = request.args.get('ano')

#    if (disciplina and isinstance(disciplina, int)) and (ano and isinstance(ano, int)):
#        questions = col_questions.find({'$or':[{'disciplina':disciplina}, {'ano':ano}]}, {'id':1,'disciplina':1,'ano':1})
#        return json_util.dumps(questions), 200
#    else if (disciplina and isinstance(disciplina, int)):
#        questions = col_questions.find({'disciplina':disciplina}, {'id':1,'disciplina':1,'ano':1})
#        return json_util.dumps(questions), 200
#    else if (ano and isinstance(ano, int)):
#        questions = col_questions.find({'ano':ano}, {'id':1,'disciplina':1,'ano':1})
#        return json_util.dumps(questions), 200
#    else:
#        return 'Os dados enviados estão inválidos', 400
        




#Opicionais

# Deletar usuarios
@app.route('/v1/delete', methods=['GET'])
def delete_users():
    col_users.remove()
    return 'OK'

#Deletar campo comment na question
@app.route('/v1/removecomment/<question_id>', methods=['GET'])
def remove_field_comment(question_id):
    question = col_questions.find_one({'id':question_id})
    col_questions.update_one({'id':question_id}, {'$unset':{'comments':1}})

    return 'OK'