#!/web/cs2041/bin/python3.6.3

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os, re
import codecs
from collections import OrderedDict
from flask import Flask, render_template, session, send_from_directory, request

students_dir = "dataset-medium"
key_hidden = ['email', 'password', 'home_latitude', 'home_longitude', 'courses', 'n']
check_icon = set()

app = Flask(__name__)


# User class
class User:
    def __init__(self, zid):
        self.zid = zid
        self.full_name = ''
        self.have_icon = have_icon(self.zid)
        if self.have_icon:
            check_icon.add(self.zid)
        self.info_dict = OrderedDict([('program', ''), ('birthday', ''), ('home_suburb', '')])
        self.friends = {}
        # init
        self.read_user_file()
        self.posts = []

    # read user posts
    # input: student zid
    # return: a list of Post Objects
    def read_post(self):
        i = 0
        posts = []
        post_path = students_dir + '/' + self.zid + '/' + str(i) + '.txt'
        while os.path.isfile(post_path):
            with open(post_path, encoding="utf8") as f:
                longitude = ""
                latitude = ""
                for line in f.readlines():
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()

                    if key == 'from':
                        zid_from = val
                    elif key == 'time':
                        time = val
                    elif key == 'message':
                        r = '<br />'
                        val = val.replace('\\n', r)
                        message = val
                    elif key == 'longitude':
                        longitude = val
                    elif key == 'latitude':
                        latitude = val
            post = Post(zid_from, time, message, longitude, latitude)
            post.have_icon = self.have_icon
            posts.append(post)

            j = 0
            comment_path = students_dir + '/' + self.zid + '/' + str(i) + '-' + str(j) + '.txt'
            while os.path.isfile(comment_path):
                with open(comment_path, encoding="utf8") as f:
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
                post.insert_comment(zid_from, time, message)
                comment = post.comments[-1]

                k = 0
                reply_path = students_dir + '/' + self.zid + '/' + str(i) + '-' + str(j) + '-' + str(k) + '.txt'
                while os.path.isfile(reply_path):
                    with open(reply_path, encoding="utf8") as f:
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
                    comment.insert_reply(zid_from, time, message)
                    k += 1
                    reply_path = students_dir + '/' + self.zid + '/' + str(i) + '-' + str(j) + '-' + str(k) + '.txt'

                j += 1
                comment_path = students_dir + '/' + self.zid + '/' + str(i) + '-' + str(j) + '.txt'

            i += 1
            post_path = students_dir + '/' + self.zid + '/' + str(i) + '.txt'
        self.posts = posts

    # read user file
    # and init self.info_dict and self.friends
    def read_user_file(self):
        details_filename = os.path.join(students_dir, self.zid, "student.txt")
        with open(details_filename, encoding="utf8") as f:
            details = f.readlines()
        for line in details:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip()
            if key != 'zid':
                if key == 'friends':
                    for friend_zid in val[1:-1].split(','):
                        friend_zid = friend_zid.strip()
                        self.friends[friend_zid] = Friend(friend_zid)
                elif key == 'full_name':
                    self.full_name = val
                else:
                    self.info_dict[key] = val


class Friend:
    def __init__(self, zid):
        self.zid = zid
        self.full_name = ''
        self.have_icon=have_icon(self.zid)
        if self.have_icon:
            check_icon.add(self.zid)
        self.read_friend_file()
        self.posts = self.read_friend_post()

    def read_friend_post(self):
        i = 0
        posts = []
        post_path = students_dir + '/' + self.zid + '/' + str(i) + '.txt'
        while os.path.isfile(post_path):
            with open(post_path, encoding="utf8") as f:
                longitude = ""
                latitude = ""
                for line in f.readlines():
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()

                    if key == 'from':
                        zid_from = val
                    elif key == 'time':
                        time = val
                    elif key == 'message':
                        r = '<br />'
                        val = val.replace('\\n', r)
                        message = val
                    elif key == 'longitude':
                        longitude = val
                    elif key == 'latitude':
                        latitude = val
            post = Post(zid_from, time, message, longitude, latitude)
            post.have_icon = self.have_icon
            posts.append(post)

            j = 0
            comment_path = students_dir + '/' + self.zid + '/' + str(i) + '-' + str(j) + '.txt'
            while os.path.isfile(comment_path):
                with open(comment_path, encoding="utf8") as f:
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
                post.insert_comment(zid_from, time, message)
                comment = post.comments[-1]

                k = 0
                reply_path = students_dir + '/' + self.zid + '/' + str(i) + '-' + str(j) + '-' + str(k) + '.txt'
                while os.path.isfile(reply_path):
                    with open(reply_path, encoding="utf8") as f:
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
                    comment.insert_reply(zid_from, time, message)
                    k += 1
                    reply_path = students_dir + '/' + self.zid + '/' + str(i) + '-' + str(j) + '-' + str(k) + '.txt'

                j += 1
                comment_path = students_dir + '/' + self.zid + '/' + str(i) + '-' + str(j) + '.txt'

            i += 1
            post_path = students_dir + '/' + self.zid + '/' + str(i) + '.txt'
        return posts

    def read_friend_file(self):
        details_filename = os.path.join(students_dir, self.zid, "student.txt")
        with open(details_filename, encoding="utf8") as f:
            details = f.readlines()
        for line in details:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip()
            if key == 'full_name':
                self.full_name = val



class Post:
    def __init__(self, zid, time, message, longitude='', latitude=''):
        self.zid = zid
        self.time = time
        self.message = message
        self.have_icon = False
        self.longitude = longitude
        self.latitude = latitude
        self.comments = []

    def insert_comment(self, zid, time, message=""):
        self.comments.append(Comment(zid, time, message))


class Comment:
    def __init__(self, zid, time, message):
        self.zid = zid
        self.time = time
        self.message = message
        if self.zid in check_icon:
            self.have_icon = True
        else:
            self.have_icon = False
        self.replies = []

    def insert_reply(self, zid, time, message=""):
        self.replies.append(Reply(zid, time, message))


class Reply:
    def __init__(self, zid, time, message):
        self.zid = zid
        self.time = time
        self.message = message
        if self.zid in check_icon:
            self.have_icon = True
        else:
            self.have_icon = False


def read_post(zid):
    i = 0
    posts = []
    post_path = students_dir + '/' + zid + '/' + str(i) + '.txt'
    while os.path.isfile(post_path):
        with open(post_path, encoding="utf8") as f:
            for line in f.readlines():
                key, val = line.split(':', 1)
                key = key.strip()
                val = val.strip()
                longitude = ""
                latitude = ""
                if key == 'from':
                    zid_from = val
                elif key == 'time':
                    time = val
                elif key == 'message':
                    r = '<br />'
                    val = val.replace('\\n', r)
                    message = val
                elif key == 'longitude':
                    longitude = val
                elif key == 'latitude':
                    latitude = val
        post = Post(zid_from, time, message, longitude, latitude)
        posts.append(post)

        j = 0
        comment_path = students_dir + '/' + zid + '/' + str(i) + '-' + str(j) + '.txt'
        while os.path.isfile(comment_path):
            with open(comment_path, encoding="utf8") as f:
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
            post.insert_comment(zid_from, time, message)
            comment = post.comments[-1]

            k = 0
            reply_path = students_dir + '/' + zid + '/' + str(i) + '-' + str(j) + '-' + str(k) + '.txt'
            while os.path.isfile(reply_path):
                with open(reply_path, encoding="utf8") as f:
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
                comment.insert_reply(zid_from, time, message)
                k += 1
                reply_path = students_dir + '/' + zid + '/' + str(i) + '-' + str(j) + '-' + str(k) + '.txt'

            j += 1
            comment_path = students_dir + '/' + zid + '/' + str(i) + '-' + str(j) + '.txt'

        i += 1
        post_path = students_dir + '/' + zid + '/' + str(i) + '.txt'
    return posts


# read user file
# save it in session
def read_user_file(student_to_show):
    details_filename = os.path.join(students_dir, student_to_show, "student.txt")
    with open(details_filename, encoding="utf8") as f:
        details = f.readlines()
    for line in details:
        key, val = line.split(':', 1)
        session[key] = val

def have_icon(zid):
    if os.path.isfile(students_dir + '/' + zid + '/img.jpg'):
        return True
    else:
        return False

# Show unformatted details for student "n"
# Increment n and store it in the session cookie

@app.route('/', methods=['GET', 'POST'])
@app.route('/start', methods=['GET', 'POST'])
def start():
    # if 'n' in session:
    #     n = session['n']
    # else:
    #     n = 0
    # students = sorted(os.listdir(students_dir))
    # student_to_show = students[n % len(students)]
    # user = User(student_to_show)
    # session['n'] = n + 1
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
    return send_from_directory(students_dir, filename)


@app.route('/login', methods=['POST'])
def login():
    zid = request.form.get('zid', '')
    password = request.form.get('password', '')
    # store zid in session cookie
    if zid in os.listdir(students_dir):
        user = User(zid)
        if user.info_dict['password']==password:
            session['logged_in']=zid
            return start()
    return render_template('login.html',error='Wrong zid and password combination!')

@app.route('/zid/<friend_zid>', methods=['POST','GET'])
def friends_page(friend_zid):
    if 'logged_in' in session:
        friend=User(friend_zid)
        friend.read_post()
        return render_template('start.html',
                               key_hidden=key_hidden,
                               user=friend)
    else:
        return render_template('login.html',error='')

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
