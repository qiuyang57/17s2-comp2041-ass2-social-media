#!/web/cs2041/bin/python3.6.3

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os
import sqlite3
from functools import wraps

from flask import g
from flask import Flask, render_template, session, send_from_directory, request, url_for, redirect

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine


data_folder_name = "dataset-medium"

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'database/{}.db'.format(data_folder_name)),
    SECRET_KEY='yang_qiu',
    USERNAME='admin',
    PASSWORD='default'
))
# app.config.from_envvar('FLASKR_SETTINGS', silent=True)

# Database


Base = automap_base()
engine = create_engine("sqlite:///database/{}.db".format(data_folder_name))

# reflect the tables
Base.prepare(engine, reflect=True)
User = Base.classes.user
Friend = Base.classes.friends
Enrollment = Base.classes.enrollment
Post = Base.classes.post
Comment = Base.classes.comment
Reply = Base.classes.reply
db_session = Session(engine)

# some global data
key_hidden = ['email', 'password', 'home_latitude', 'home_longitude', 'courses']

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'logged_in' in session:
        zid=session['logged_in']
        user=User(zid)
        user.read_post()
        return render_template('start.html',
                               key_hidden=key_hidden,
                               user=user)
    else:
        return render_template('login.html',error='')


@app.route('/image/<path:filename>')
def custom_static(filename):
    return send_from_directory(data_folder_name, filename)

@app.route('/profile_img/<zid>')
def profile_img(zid):
    return send_from_directory('static/profile_img/'+zid, 'img.jpg')

@app.route('/login', methods=['POST','GET'])
def login():
    error=''
    if g.user:
        return redirect(url_for('home'))
    if request.method == 'POST':
        zid = request.form.get('zid', '')
        password = request.form.get('password', '')
        user = User.query.filter(User.zid == zid)
        # store zid in session cookie
        if user is None:
            user_sus = User_suspend.query.filter(User.zid == zid)
            if user:
                error = 'User suspended!'
            else:
                error = 'Please sign up.'
        elif user.password==password:
                session['logged_in']=zid
                session['full_name']=user.full_name
                return redirect(url_for('home'))
        else:
            error='Wrong zid and password combination!'
    return render_template('login.html',error=error)

@app.route('/logout')
def logout():
    if 'logged_in' in session:
        session.pop('logged_in')
        session.pop('full_name')
    return render_template('login.html',error='You successful logout!')

@app.route('/zid/<user_zid>', methods=['POST', 'GET'])
def user_page(user_zid):
    if 'logged_in' in session:
        user=User.query.filter(User.zid==user_zid)
        return render_template('start.html',
                               key_hidden=key_hidden,
                               user=user)
    else:
        return render_template('login.html',error='')

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
