# * ---------- IMPORTS --------- *
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import os
import psycopg2
import cv2
import numpy as np
import re
from flask_pymongo import PyMongo


# Get the relativ path to this file (we will use it later)
FILE_PATH = os.path.dirname(os.path.realpath(__file__))

# * ---------- Create App --------- *
app = Flask(__name__)
CORS(app, support_credentials=True)



# * ---------- DATABASE CONFIG --------- *

app.config['MONGO_DBNAME'] = 'faceRecognition'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/faceRecognition'

mongo = PyMongo(app)

# * --------------------  ROUTES ------------------- *
# * ---------- Get data from the face recognition ---------- *
@app.route('/receive_data', methods=['POST'])
def get_receive_data():
    if request.method == 'POST':
        json_data = request.get_json()

        usersDB = mongo.db.users
        if usersDB:
            print('user IN')
            image_path = f"{FILE_PATH}/assets/img/{json_data['date']}/{json_data['name']}/departure.jpg"

            # Save image
            os.makedirs(f"{FILE_PATH}/assets/img/{json_data['date']}/{json_data['name']}", exist_ok=True)
            cv2.imwrite(image_path, np.array(json_data['picture_array']))
            json_data['picture_path'] = image_path
            existingUser = usersDB.find_one({"name":json_data['name']})
            existingUser['time']=json_data['hour']
            existingUser['departure_pic']=json_data['picture_path']
            usersDB.save(existingUser)

        else:
            print("user OUT")
            # Save image
            image_path = f"{FILE_PATH}/assets/img/history/{json_data['date']}/{json_data['name']}/arrival.jpg"
            os.makedirs(f"{FILE_PATH}/assets/img/history/{json_data['date']}/{json_data['name']}", exist_ok=True)
            cv2.imwrite(image_path, np.array(json_data['picture_array']))
            json_data['picture_path'] = image_path

            # Create a new row for the user today:
            usersDB.insert({
                "name":json_data['name'],
                "date":json_data['date'],
                "arrival_time":json_data['hour'],
                "arrival_picture":json_data['picture_path']
            })
        return jsonify(json_data)


# # * ---------- Get all the data of an employee ---------- *
@app.route('/get_employee/<string:name>', methods=['GET'])
def get_employee(name):
    answer_to_send = {}
    # Check if the user is already in the DB
    user_info = mongo.db.users.find_one({"name":name})
    if user_info:
        print('RESULT: ',user_info)
        # Structure the data and put the dates in string for the front
        for k,v in enumerate(user_info):
            answer_to_send[k] = {}
            for ko,vo in enumerate(user_info[k]):
                answer_to_send[k][ko] = str(vo)
        print('answer_to_send: ', answer_to_send)
    else:
        answer_to_send = {'error': 'User not found...'}
    return jsonify(answer_to_send)


# * --------- Get the 5 last users seen by the camera --------- *
@app.route('/get_5_last_entries', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_5_last_entries():
    answer_to_send = {}
    # Check if the user is already in the DB
    latest_entries = mongo.db.users.find({})
    results = []
    for i in latest_entries:
        results.append(i)

    # if DB is not empty:
    if results:
        # Structure the data and put the dates in string for the front
        for k, v in enumerate(results):
            answer_to_send[k] = {}
            for ko, vo in enumerate(results[k]):
                answer_to_send[k][ko] = str(v[vo])
    else:
        answer_to_send = {'error': 'error detect'}
    return jsonify(answer_to_send)


# * ---------- Add new employee ---------- *
@app.route('/add_employee', methods=['POST'])
@cross_origin(supports_credentials=True)
def add_employee():
    try:
        # Get the picture from the request
        image_file = request.files['image']
        print(request.form['nameOfEmployee'])

        # Store it in the folder of the know faces:
        file_path = os.path.join(f"assets/img/users/{request.form['nameOfEmployee']}.jpg")
        image_file.save(file_path)
        answer = 'new employee succesfully added'
    except:
        answer = 'Error while adding new employee. Please try later...'
    return jsonify(answer)


# * ---------- Get employee list ---------- *
@app.route('/get_employee_list', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_employee_list():
    employee_list = {}

    # Walk in the user folder to get the user list
    walk_count = 0
    for file_name in os.listdir(f"{FILE_PATH}/assets/img/users/"):
        # Capture the employee's name with the file's name
        name = re.findall("(.*)\.jpg", file_name)
        if name:
            employee_list[walk_count] = name[0]
        walk_count += 1

    return jsonify(employee_list)


# * ---------- Delete employee ---------- *
@app.route('/delete_employee/<string:name>', methods=['GET'])
def delete_employee(name):
    try:
        # Remove the picture of the employee from the user's folder:
        print('name: ', name)
        file_path = os.path.join(f'assets/img/users/{name}.jpg')
        os.remove(file_path)
        answer = 'Employee succesfully removed'
    except:
        answer = 'Error while deleting new employee. Please try later'

    return jsonify(answer)

# * -------------------- RUN SERVER -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
    #  * --- DOCKER PRODUCTION MODE: --- *
    # app.run(host='0.0.0.0', port=os.environ['PORT']) -> DOCKER
