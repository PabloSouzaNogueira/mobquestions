from flask import Flask, request, jsonify, redirect
from flask_pymongo import PyMongo

from werkzeug.security import generate_password_hash, check_password_hash

from bson import json_util

from config import MONGO_URI
from auth import *

import os
import redis

os.getenv('FLASK_TESTING')=='1'

rcache = redis.Redis(
            host='redis-19130.c1.ap-southeast-1-1.ec2.cloud.redislabs.com', 
            port=19130,
            password='4NdaP8ra7wuj2lZOfGK5Yi1Et8JhQX45')


app = Flask(__name__)
app.config['MONGO_URI'] = MONGO_URI
app.config['DEBUG'] = True

app_context = app.app_context()
app_context.push()

mongo = PyMongo(app)

col_users = mongo.db.users
col_questions = mongo.db.questions
col_tokens = mongo.db.tokens 


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



@app.route('/', methods=['GET'])
#@jwt_required
def index():
    res = col_users.find({})
    return json_util.dumps(list(res)), 200





# Atividades

#Exercício 00
@app.route('/v1/users/', methods=['POST'])
def insert_user():
    data = request.get_json()

    if 'username' not in data:
        return 'Favor informar o username', 400

    res = col_users.find({'username':data['username']})

    if (len(list(res)) > 0):
        return 'Usuário ' + data['username'] + ' já existe!', 203
    else:
        data['password'] = generate_password_hash(data['password'])
        col_users.insert_one(data)
        return 'Usuário ' + data['username'] + ' criado!', 201

#Exercício 01
@app.route('/v1/users/<username>', methods=['GET'])
def search_user(username):
    res = col_users.find({'username':username})
    
    if (len(list(res)) > 0):
        res = col_users.find({'username':username})
        return json_util.dumps(res), 200
    else:
        return 'Usuário ' + username + ' não existe!', 404

#Exercício 02
@app.route('/v1/user/authenticate', methods=['POST'])
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
@app.route('/v1/user/update/<username>', methods=['PUT']) 
@jwt_required
def update_user(username):
    data = request.get_json()

    if not username:
        return 'Favor informar o nome do usuário.', 401

    usuario = col_users.find_one({'username':username})

    if not usuario:
        return 'Não existe usuário ' + username, 401
    
    if 'name' in data and data['name']:
        col_users.update_one({'username':username}, {'$set':{'name': data['name']} })
    if 'email' in data and data['email']:
        col_users.update_one({'username':username}, {'$set':{'email': data['email']} })
    if 'phones' in data and data['phones']:
        col_users.update_one({'username':username}, {'$set':{'phones': data['phones']} })
        
    return 'Usuário atualizado!', 200          

#Exercicio04
@app.route('/v1/user/updatepassword/<username>', methods=['PATCH'])
def update_password_user(username):
    data = request.get_json()

    if username:
        user = col_users.find_one({'username':username})
        if user:
            hash_password = generate_password_hash(data['password'])
            col_users.update_one({'username':username}, {'$set':{'password': hash_password}})
            return 'Senha atualizada!', 200
        else:
            return 'Não existe usuário ' + username, 403
    else:
        return 'Favor informar usuário.', 401

#Exercicio05
@app.route('/v1/questions/<question_id>', methods=['GET'])
def get_question(question_id):
    question = col_questions.find_one({'id':question_id})

    if question:
        return json_util.dumps(question), 200
    else:
        return 'Não foi possível encontrar esta questão!', 404


#Exercício06
@app.route('/v1/comment', methods=['POST'])
@jwt_required
def set_comment_question():
    data = request.get_json()
    question = col_questions.find_one({'id':data['question_id']})
    user = col_users.find_one({'username':data['username']})

    if question:
        if (user and data['message']):
            
            if 'comments' not in question:
                comment = []
                comment.append({'username': data['username'], 'message': data['message']})
                col_questions.update_one({'id':data['question_id']}, {'$set':{'comments':comment}})
            else:
                comment = {'username': data['username'], 'message': data['message']}
                col_questions.update_one({'id':data['question_id']}, {'$push':{'comments':comment}})

            question = col_questions.find_one({'id':data['question_id']})
            return json_util.dumps(question), 200

        else:
            return 'Usuário não existe ou os dados informados são inválidos', 401
    else:
        return 'Não foi possível encontrar esta questão!', 404


#Exercicio07
@app.route('/v1/questions/search/', methods=['GET'])
def search_questions():
    disciplina = request.args.get('disciplina')
    ano = request.args.get('ano')

    if disciplina and ano :
        try:
            conv_disciplina = int(disciplina)
            conv_ano = int(ano)  
            questions = col_questions.find({'$or':[{'disciplina':conv_disciplina}, {'ano':conv_ano}]}, {'id':1,'disciplina':1,'ano':1})
            return json_util.dumps(questions), 200
        except:
            return 'Os dados enviados estão inválidos ', 400
        
    elif disciplina :
        try:
            conv_disciplina = int(disciplina)
            questions = col_questions.find({'disciplina':conv_disciplina}, {'id':1,'disciplina':1,'ano':1})
            return json_util.dumps(questions), 200
        except:
            return 'Os dados enviados estão inválidos ', 400
    elif ano :
        try:
            conv_ano = int(ano)
            questions = col_questions.find({'ano':conv_ano}, {'id':1,'disciplina':1,'ano':1})
            return json_util.dumps(questions), 200
        except:
            return 'Os dados enviados estão inválidos', 400
    else:
        return 'Os dados enviados estão inválidos', 400
        

#Exercicio09
@app.route('/v1/questions/answer/<question_id>', methods=['POST'])
def set_answer_question(question_id):
    data = request.get_json()
    user = col_users.find_one({'username':data['username']})
    question = col_questions.find_one({'id':question_id})

    if not user:
        return 'Não existe usuário ' + data['username'], 401
    
    if not question:
        return 'Não existe a questão' + question_id, 401

    if not data['answer']:
        return 'Favor informar uma resposta', 401


    if 'answers' not in user:
        answers = []
        answers.append({'question_id': question_id, 'answer': data['answer']})
        col_users.update_one({'username':data['username']}, {'$set':{'answers':answers}})

    else:
        answers = {'question_id': question_id, 'answer': data['answer']}
        question_in_user = col_users.find_one({'username':data['username'] , 'answers': {'$elemMatch': {'question_id': question_id} } })

        if question_in_user:
            col_users.update_one({'username':data['username'], "answers.question_id" : question_id }, {'$set':{'answers.$.answer':data['answer']}})
        else:
            col_users.update_one({'username':data['username']}, {'$push':{'answers':answers}})
    

    if 'contador_resposta' in question:
        contador_resposta = 1 + question['contador_resposta']
        col_questions.update_one({'id':question_id},{'$set':{'contador_resposta':contador_resposta}})
    else:
        col_questions.update_one({'id':question_id},{'$set':{'contador_resposta':1}})
        
    
    if question['resposta'] == data['answer']:
        return 'Resposta correta!', 200
    else:
        return 'Resposta errada!', 200  


#Exercicio10
@app.route('/v1/questions/answers', methods=['GET'])
@jwt_required
def search_answers_question():
    user_autenticado = g.parsed_token

    user = col_users.find_one({'username':user_autenticado['username']}, {'answers':1})

    if user:
        return json_util.dumps(user), 200
    else:
        return 'Este usuário não respondeu nenhuma questão.', 404


#Exercicio11
@app.route('/v1/featured_questions', methods=['POST'])
def update_cache_question():
    featured_questions = col_questions.find({'contador_resposta': { '$gt': 0 }}).sort([('contador_resposta',-1)]).limit(5)
    
    if rcache:
        rcache.set('featured_questions', json_util.dumps(featured_questions))
    
    featured_questions = col_questions.find({'contador_resposta': { '$gt': 0 }}).sort([('contador_resposta',-1)]).limit(5)

    return json_util.dumps(featured_questions), 200

#Exercicio12
@app.route('/v1/featured_questions', methods=['GET'])
def get_cache_question():   
    if rcache and rcache.get('featured_questions'):
        return rcache.get('featured_questions'), 200
    else:
        featured_questions = col_questions.find({'contador_resposta': { '$gt': 0 }}).sort([('contador_resposta',-1)]).limit(5)  
        return json_util.dumps(featured_questions), 203

#Opicionais

# Deletar usuarios
@app.route('/v1/delete/users', methods=['GET'])
def delete_users():
    col_users.remove()
    return 'OK', 200

#Deletar campo comment na question
@app.route('/v1/removecomment/<question_id>', methods=['GET'])
def remove_field_comment(question_id):
    question = col_users.find_one({'username':question_id})
    col_users.update_one({'username':question_id}, {'$unset':{'answers':1}})
    return 'OK', 200


@app.route('/v1/pablo/allquestions', methods=['GET'])
def get_allquestion():
    question = col_questions.find({},{'id':1, 'disciplina':1})

    if question:
        return json_util.dumps(question), 200
    else:
        return 'Não foi possível encontrar as questões!', 404