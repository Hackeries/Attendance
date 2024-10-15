# app.py
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import concurrent.futures

load_dotenv()

app = Flask(__name__)
CORS(app)

stu_profiles = [
    {
        "username": "e22cseu____@bennett.edu.in",
        "password": "",
        "name": "",
        "category": ["Automata", "AI"]
    }
]

def get_cookies(username, password):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-GB,en;q=0.8',
        'clienttzofst': '330',
        'content-type': 'application/json',
        'origin': 'https://student.bennetterp.camu.in',
        'priority': 'u=1, i',
        'referer': 'https://student.bennetterp.camu.in/v2/?id=663474b11dd0e9412a1f793f',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sec-gpc': '1',
    }

    json_data = {
        'dtype': 'M',
        'Email': username,
        'pwd': password,
    }

    response = requests.post('https://student.bennetterp.camu.in/login/validate', headers=headers, json=json_data)
    stu_id = response.json()["output"]["data"]["logindetails"]["Student"][0]["StuID"]
    cookie = response.headers["Set-Cookie"].split(";")[0].split("=")[1]
    return cookie, stu_id

def mark_attendance(stu_id, cookie, qr_code):
    cookies = {
        'connect.sid': cookie,
    }

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-GB,en;q=0.8',
        'clienttzofst': '330',
        'content-type': 'application/json',
        'origin': 'https://student.bennetterp.camu.in',
        'priority': 'u=1, i',
        'referer': 'https://student.bennetterp.camu.in/v2/timetable',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sec-gpc': '1',
    }

    json_data = {
        'attendanceId': qr_code,
        'StuID': stu_id,
        'offQrCdEnbld': True,
    }

    response = requests.post(
        'https://student.bennetterp.camu.in/api/Attendance/record-online-attendance',
        cookies=cookies,
        headers=headers,
        json=json_data,
    )
    
    return response.json()["output"]["data"]["code"]

def process_student(student, qr_code):
    try:
        cookie, stu_id = get_cookies(student["username"], student["password"])
        response = mark_attendance(stu_id, cookie, qr_code)
        return f"{student['name']}: {response}\n"
    except Exception as e:
        return f"{student['name']}: Error - {str(e)}\n"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance_route():
    data = request.json
    category = data['category']
    qr_code = data['qr_code']

    def generate():
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for student in stu_profiles:
                if category in student["category"]:
                    futures.append(executor.submit(process_student, student, qr_code))
            
            for future in concurrent.futures.as_completed(futures):
                yield future.result()

    return Response(generate(), content_type='text/plain')

if __name__ == '__main__':
    app.run(debug=True, port=5100)
