from flask import Flask, request,render_template,url_for,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_jsonpify import jsonify
import asyncio
from aiohttp import ClientSession
import os, requests
from generate_keys import *
from generate_keys import encrypt
from generate_keys import format_key
from generate_keys import decrypt
from generate_keys import generate_key_pair
from flask_cors import CORS

app = Flask(__name__)

basedir=os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]='sqlite:///'+os.path.join(basedir+'crypto.db')
app.config['SECRET_KEY'] = 'MYLITTLESECRETKEY'
db=SQLAlchemy(app)
CORS(app)

##########models########################

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    surname = db.Column(db.String(100))
    username = db.Column(db.String(100))
    tc_no = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(100))
    public_key = db.Column(db.String(9000))
    private_key = db.Column(db.String(9000))

class HealthDataProvider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500))
    base_url = db.Column(db.String(500))
    type = db.Column(db.String(20))

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    hospital_name = db.Column(db.String(1000))
    clinic_name = db.Column(db.String(1000))
    doctor_name = db.Column(db.String(1000))

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    date = db.Column(db.String(1000))
    prescription_number = db.Column(db.String(1000))
    prescription_type = db.Column(db.String(1000))
    doctor = db.Column(db.String(1000))

class Prescription_Details(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey(Prescription.id))
    barcode = db.Column(db.String(1000))
    medicine_name = db.Column(db.String(1000))
    description = db.Column(db.String(1000))
    dosage = db.Column(db.String(1000))
    period = db.Column(db.String(1000))
    usage = db.Column(db.String(1000))
    usage_count = db.Column(db.String(1000))
    box_count = db.Column(db.String(1000))


class MedicalReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    date = db.Column(db.String(1000))
    report_number = db.Column(db.String(1000))
    report_type = db.Column(db.String(1000))
    start_date = db.Column(db.String(1000))
    end_date = db.Column(db.String(1000))
    diagnosis = db.Column(db.String(1000))

class Illness(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    date = db.Column(db.String(1000))
    diagnosis = db.Column(db.String(1000))
    department = db.Column(db.String(1000))
    doctor = db.Column(db.String(1000))

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    name = db.Column(db.String(1000))
    result = db.Column(db.String(1000))
    result_unit = db.Column(db.String(1000))
    reference_value = db.Column(db.String(1000))
    date = db.Column(db.String(1000))


db.create_all()
##################################

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/login')
def login():
    return render_template('login.html')
@app.route('/showSignUp')
def showSignUp():
    return render_template('signup.html')
@app.route('/userr')
def userr():
    userlist=User.query.all()
    return render_template('users.html',data=userlist)

@app.route('/request_user_key/<user_id>', methods=['GET','POST'])
def request_user_key(user_id):
    u = get_user(user_id)
    object_to_return = {}
    object_to_return['username'] = u.username
    object_to_return['private_key'] = u.private_key
    object_to_return['public_key'] = u.public_key

    return jsonify(object_to_return)

@app.route('/signUp', methods=['GET','POST'])
def sign_up():
    _name = request.form['name']
    _surname = request.form['surname']
    _username = request.form['username']
    _password = request.form['password']
    _tc_no = request.form['tcno']
    
    

    private_key, public_key = generate_key_pair()
    sifrename=encrypt(public_key,_name)
    sifresurname=encrypt(public_key,_surname)
    sifreusername=encrypt(public_key,_username)
    sifrepassword=encrypt(public_key,_password)
    sifretc=encrypt(public_key,_tc_no)

    user = User(name=sifrename,
                surname=sifresurname,
                username = sifreusername,
                password = sifrepassword,
                tc_no=sifretc,
                public_key=public_key,
                private_key=private_key
                )

    db.session.add(user)
    db.session.commit()


    object_to_return = {}
    object_to_return['username']=str(sifresurname)
    object_to_return['private_key']=  private_key
    object_to_return['public_key'] =  public_key
    object_to_return['user_id'] = user.id
    return jsonify(object_to_return)

@app.route('/request_all_visit/<user_id>', methods=['GET', 'POST'])
def request_all_visit(user_id):
    data_providers = HealthDataProvider.query.all()
    visit_tasks=[]
    loop = asyncio.get_event_loop()
    for dp in data_providers.items:
        url = dp.base_url + 'get_visit_for/'+user_id
        task = asyncio.ensure_future(get_visit_from_remote(url))
        visit_tasks.append(task)
    loop.run_until_complete(asyncio.wait(visit_tasks))



@app.route('/get_visit/<user_id>', methods=['GET','POST'])
def search_visit(user_id):
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('_limit', type=int, default=15)
    sort = request.args.get('_sort', type=str, default='id')
    order = request.args.get('_order', type=str, default='ASC')

    if (order == 'ASC'):
        s = Visit.query.filter_by(user_id=user_id).order_by(getattr(Visit, sort).asc()).paginate(
            page=page, per_page=per_page)
    else:
        s = Visit.query.filter_by(user_id=user_id).order_by(getattr(Visit, sort).desc()).paginate(
            page=page, per_page=per_page)

    return_object = {}
    return_object['count'] = s.total
    return_object['per_page'] = s.per_page
    return_object['page'] = s.page
    return_object['total_pages'] = s.pages
    return_object['success'] = True
    return_list = []

    for visit in s.items:
        return_list_item = {'id': visit.id}
        return_list.append(return_list_item)
    return_object['data'] = return_list

    return jsonify(return_object)

@app.route('/insert_visit/<user_id>', methods=['POST'])
def insert_visit(user_id):
    hospital_name = request.json['hospital_name']
    clinic_name = request.json['clinic_name']
    doctor_name = request.json['doctor_name']
    user = get_user(user_id)
    visit = Visit(user_id=user_id,
                  hospital_name=encrypt(user.public_key, hospital_name),
                  clinic_name = encrypt(user.public_key, clinic_name),
                  doctor_name = encrypt(user.public_key, doctor_name)
                  )
    db.session.add(visit)
    db.session.commit()
    return  jsonify({})



@app.route('/get_prescription/<user_id>', methods=['GET','POST'])
def search_prescription(user_id):
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('_limit', type=int, default=15)
    sort = request.args.get('_sort', type=str, default='id')
    order = request.args.get('_order', type=str, default='ASC')

    if (order == 'ASC'):
        s = Visit.query.filter_by(user_id=user_id).order_by(getattr(Prescription, sort).asc()).paginate(
            page=page, per_page=per_page)
    else:
        s = Visit.query.filter_by(user_id=user_id).order_by(getattr(Prescription, sort).desc()).paginate(
            page=page, per_page=per_page)

    return_object = {}
    return_object['count'] = s.total
    return_object['per_page'] = s.per_page
    return_object['page'] = s.page
    return_object['total_pages'] = s.pages
    return_object['success'] = True
    return_list = []

    for prescription in s.items:
        return_list_item = {'id': prescription.id}
        return_list.append(return_list_item)
    return_object['data'] = return_list

    return jsonify(return_object)

@app.route('/get_medical_report/<user_id>', methods=['GET','POST'])
def search_medical_report(user_id):
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('_limit', type=int, default=15)
    sort = request.args.get('_sort', type=str, default='id')
    order = request.args.get('_order', type=str, default='ASC')

    if (order == 'ASC'):
        s = Visit.query.filter_by(user_id=user_id).order_by(getattr(MedicalReport, sort).asc()).paginate(
            page=page, per_page=per_page)
    else:
        s = Visit.query.filter_by(user_id=user_id).order_by(getattr(MedicalReport, sort).desc()).paginate(
            page=page, per_page=per_page)

    return_object = {}
    return_object['count'] = s.total
    return_object['per_page'] = s.per_page
    return_object['page'] = s.page
    return_object['total_pages'] = s.pages
    return_object['success'] = True
    return_list = []

    for medical_report in s.items:
        return_list_item = {'id': medical_report.id}
        return_list.append(return_list_item)
    return_object['data'] = return_list

    return jsonify(return_object)


@app.route('/get_illness/<user_id>', methods=['GET','POST'])
def search_illness(user_id):
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('_limit', type=int, default=15)
    sort = request.args.get('_sort', type=str, default='id')
    order = request.args.get('_order', type=str, default='ASC')

    if (order == 'ASC'):
        s = Visit.query.filter_by(user_id=user_id).order_by(getattr(Illness, sort).asc()).paginate(
            page=page, per_page=per_page)
    else:
        s = Visit.query.filter_by(user_id=user_id).order_by(getattr(Illness, sort).desc()).paginate(
            page=page, per_page=per_page)

    return_object = {}
    return_object['count'] = s.total
    return_object['per_page'] = s.per_page
    return_object['page'] = s.page
    return_object['total_pages'] = s.pages
    return_object['success'] = True
    return_list = []

    for illness in s.items:
        return_list_item = {'id': illness.id}
        return_list.append(return_list_item)
    return_object['data'] = return_list

    return jsonify(return_object)

@app.route('/get_test_results/<user_id>', methods=['GET','POST'])
def search_test_result(user_id):
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('_limit', type=int, default=15)
    sort = request.args.get('_sort', type=str, default='id')
    order = request.args.get('_order', type=str, default='ASC')

    if (order == 'ASC'):
        s = Visit.query.filter_by(user_id=user_id).order_by(getattr(TestResult, sort).asc()).paginate(
            page=page, per_page=per_page)
    else:
        s = Visit.query.filter_by(user_id=user_id).order_by(getattr(TestResult, sort).desc()).paginate(
            page=page, per_page=per_page)

    return_object = {}
    return_object['count'] = s.total
    return_object['per_page'] = s.per_page
    return_object['page'] = s.page
    return_object['total_pages'] = s.pages
    return_object['success'] = True
    return_list = []

    for test_result in s.items:
        return_list_item = {'id': test_result.id}
        return_list.append(return_list_item)
    return_object['data'] = return_list

    return jsonify(return_object)



def get_user(user_id):
    user = User.query.get(user_id)
    return user



if __name__ == '__main__':
    app.run()
