#!/web/cs2041/bin/python3.6.3

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os, glob
from flask import Flask, render_template, session, send_from_directory, url_for

students_dir = "dataset-medium";
key_not_show = ['email','password','home_latitude','home_longitude','courses','n']
key_in_order = ['full_name','zid', 'program', 'birthday', 'home_suburb', 'friends']

app = Flask(__name__)

class Post():
    def __init__(self, zid, time, message, longitude='', latitude=''):
        self.zid = zid
        self.time = time
        self.message = message
        self.longitude = longitude
        self.latitude = latitude
        self.comments = []
    
    def insert_comment(self, zid, time, message=""):
        self.comments.append(Comment(zid, time, message))

class Comment():
    def __init__(self, zid, time, message):
        self.zid = zid
        self.time = time
        self.message = message
        self.replies = []
    
    def insert_reply(self, zid, time, message=""):
        self.replies.append(Reply(zid, time, message))

class Reply(): 
    def __init__(self, zid, time, message):
        self.zid = zid
        self.time = time
        self.message = message


# read user posts
# input: student zid
# return: a list of Post Objects
def read_post(zid):
    i = 0
    posts = []
    print(zid)
    post_path = students_dir+'/'+zid+'/'+str(i)+'.txt'
    while os.path.isfile(post_path):
        with open(post_path) as f:
            for line in f.readlines():
                key, val = line.split(':', 1)
                key = key.strip()
                val = val.strip()
                longitude=""
                latitude=""
                if key == 'from':
                    zid_from = val
                elif key == 'time':
                    time = val
                elif key == 'message':
                    r = '<br />'
                    val = val.replace('\\n',r)
                    message = val
                elif key == 'longitude':
                    longitude = val
                elif key == 'latitude':
                    latitude = val
        post = Post(zid_from, time, message, longitude, latitude)
        posts.append(post)
        
        j = 0
        comment_path = students_dir+'/'+zid+'/'+str(i)+'-'+str(j)+'.txt'
        while os.path.isfile(comment_path):
            with open(comment_path) as f:
                for line in f.readlines():
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()
                    if key == 'from':
                        zid_from = val
                    elif key == 'time':
                        time = val
                    elif key == 'message':
                        message = val
            post.insert_comment(zid_from,time,message)
            comment = post.comments[-1]

            k=0
            reply_path = students_dir+'/'+zid+'/'+str(i)+'-'+str(j)+'-'+str(k)+'.txt'
            while os.path.isfile(reply_path):
                print(k)
                with open(reply_path) as f:
                    for line in f.readlines():
                        key, val = line.split(':', 1)
                        key = key.strip()
                        val = val.strip()
                        if key == 'from':
                            zid_from = val
                        elif key == 'time':
                            time = val
                        elif key == 'message':
                            message = val
                comment.insert_reply(zid_from,time,message)
                reply = comment.replies[-1]
                k+=1
                reply_path = students_dir+'/'+zid+'/'+str(i)+'-'+str(j)+'-'+str(k)+'.txt'
            
            j+=1
            comment_path = students_dir+'/'+zid+'/'+str(i)+'-'+str(j)+'.txt'

        i += 1
        post_path = students_dir+'/'+zid+'/'+str(i)+'.txt'
    return posts

# read user file
# save it in session
def read_user_file(student_to_show):
    details_filename = os.path.join(students_dir, student_to_show, "student.txt")
    with open(details_filename) as f:
        details = f.readlines()
    for line in details:
        key, val = line.split(':', 1)
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
    posts = read_post(student_to_show)
    print(posts)
    img_path = os.path.join(student_to_show, "img.jpg")
    session['n'] = n + 1

    other_info = []
    for key in session:
        if key not in key_in_order and key not in key_not_show:
            other_info.append(key)
    return render_template('start.html',
                            other_info=other_info,
                            posts=posts,
                            img=img_path)

@app.route('/image/<path:filename>')
def custom_static(filename):
    return send_from_directory(students_dir, filename)



if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
