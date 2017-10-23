#!/web/cs2041/bin/python3.6.3

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os
from flask import Flask, render_template, session, send_from_directory, url_for

students_dir = "dataset-medium";
key_not_show = ['email','password','home_latitude','home_longitude','courses']
key_to_show = ['zid', 'program', 'birthday', 'home_suburb', 'friends']

app = Flask(__name__)

# read user file
def read_user_file(student_to_show):
    details_filename = os.path.join(students_dir, student_to_show, "student.txt")
    with open(details_filename) as f:
        details = f.readlines()
    for line in details:
        key, val = line.split(':',1)
        session[key] = val
    
# Show unformatted details for student "n"
# Increment n and store it in the session cookie

@app.route('/', methods=['GET','POST'])
@app.route('/start', methods=['GET','POST'])
def start():
    if 'n' in session:
        n = session['n']
    else:
        n = 0
    students = sorted(os.listdir(students_dir))
    student_to_show = students[n % len(students)]
    read_user_file(student_to_show)
    img_path = os.path.join(student_to_show, "img.jpg")
    session['n'] = n + 1
    return render_template('start.html', 
                            img=img_path)

@app.route('/image/<path:filename>')
def custom_static(filename):
    return send_from_directory(students_dir, filename)



if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
