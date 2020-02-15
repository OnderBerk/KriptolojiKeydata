from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_jsonpify import jsonify

import cx_Oracle
import os, requests
import re

agent = Flask(__name__)
basedir=os.path.abspath(os.path.dirname(__file__))


agent.config['SECRET_KEY'] = 'AGENTKEY'
agent.config["SQLALCHEMY_DATABASE_URI"]='sqlite:///'+os.path.join(basedir+'agent.db')
agent.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(agent)


######################MODELS##########################
class ApplicationParameter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code =db.Column(db.String(100))
    value = db.Column(db.String(100))

class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50))
    query_text = db.Column(db.String(5000))

class QueryDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer,db.ForeignKey(Query.id))
    parameter_name = db.Column(db.String(250))
    parameter_value = db.Column(db.String(50))

db.create_all()
######################################################

@agent.route('/request_visit_for/<user_id>', methods=['GET','POST'])
def request_visit(user_id):
    connection = cx_Oracle.connect('keyhbys','keydata','10.0.0.54:1521/ANKATEST')
    cursor = connection.cursor()

    pk_data = request_user_public_key(user_id)

    query = Query.query.filter_by(code='VISIT')

    qt = query.query_text.replace(':USER_ID', user_id)
    cursor.execute(qt)

    return_object = {}
    return_list = []
    for item in cursor:
        return_list.append(item)
    return_object['data'] = return_list
    return_object['success'] = True
    return_object['message'] = 'Başarılı!'
    return jsonify(return_object)




@agent.route('/insert_query', methods=['POST'])
def insert_query():
    query_text = request.json['query']
    code = request.json['code']
    return_object = {}
    if code in get_query_codes():
        print(get_query_codes())
        return_object['succes']=False
        return_object['message']=code +' ismiyle bir kayıt bulunmaktadır. '
        return jsonify(return_object)

    query = Query(code=code, query_text=query_text)
    db.session.add(query)
    db.session.commit()

    parameters = re.findall('[:]\w+',query_text)

    if parameters:
        for parameter in parameters:
            qd = QueryDetail(query_id=query.id, parameter_name=parameter)
            db.session.add(qd)
            db.session.commit()
    return_object['succes'] = True
    return_object['message'] = 'Kayıt başarılı!'
    return jsonify(return_object)

def get_query_codes():
    codes = Query.query.with_entities(Query.code).all()
    if codes:
        return codes[0]

def request_user_public_key(user_id):
    url_parameter = ApplicationParameter.query.filter_by(code='REMOTE_URL')
    url = url_parameter.value +'/get_public_key'
    r = requests.get(url, params={'user_id':user_id})
    return r.json()


if __name__=='__main__':
    agent.run(port=5001)