#!/web/cs2041/bin/python3.6.3

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os, re
from collections import OrderedDict
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, render_template, session, send_from_directory, request, url_for, redirect, g
from email.mime.text import MIMEText
import smtplib

students_dir = "dataset-medium"
key_hidden = ['email', 'password', 'home_latitude', 'home_longitude', 'courses', 'n']
# check_icon = set()
zid_name_dict={}
user_object_dict={}
user_suspend_dict={}

app = Flask(__name__)


# User class
class User:
    def __init__(self, zid):
        self.zid = zid
        self.full_name = ''
        self.have_icon = have_icon(self.zid)
        # if self.have_icon:
        #     check_icon.add(self.zid)
        self.info_dict = OrderedDict([('program', ''), ('birthday', ''), ('home_suburb', '')])
        self.friends = []
        # init
        self.courses = []
        self.read_user_file()
        self.posts = []
        self.sorted_posts = []


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
                    try:
                        key, val = line.split(':', 1)
                    except ValueError:
                        continue
                    key = key.strip()
                    val = val.strip()

                    if key == 'from':
                        zid_from = val
                    elif key == 'time':
                        time = val
                    elif key == 'message':
                        # r = '<br />'
                        # val = val.replace('\\n', r)
                        message = val
                    elif key == 'longitude':
                        longitude = val
                    elif key == 'latitude':
                        latitude = val
            self.insert_post(zid_from, time, message, longitude, latitude)
            post = self.posts[-1]
            # post.have_icon = self.have_icon

            j = 0
            comment_path = students_dir + '/' + self.zid + '/' + str(i) + '-' + str(j) + '.txt'
            while os.path.isfile(comment_path):
                with open(comment_path, encoding="utf8") as f:
                    for line in f.readlines():
                        try:
                            key, val = line.split(':', 1)
                        except ValueError:
                            continue
                        key = key.strip()
                        val = val.strip()
                        if key == 'from':
                            zid_from = val
                        elif key == 'time':
                            time = val
                        elif key == 'message':
                            # r = '<br />'
                            # val = val.replace('\\n', r)
                            message = val
                post.insert_comment(zid_from, time, message)
                comment = post.comments[-1]

                k = 0
                reply_path = students_dir + '/' + self.zid + '/' + str(i) + '-' + str(j) + '-' + str(k) + '.txt'
                while os.path.isfile(reply_path):
                    with open(reply_path, encoding="utf8") as f:
                        for line in f.readlines():
                            try:
                                key, val = line.split(':', 1)
                            except ValueError:
                                continue
                            key = key.strip()
                            val = val.strip()
                            if key == 'from':
                                zid_from = val
                            elif key == 'time':
                                time = val
                            elif key == 'message':
                                # r = '<br />'
                                # val = val.replace('\\n', r)
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
            key, val = line.split(': ', 1)
            key = key.strip()
            val = val.strip()
            if key != 'zid':
                if key == 'friends':
                    for friend_zid in val[1:-1].split(','):
                        friend_zid = friend_zid.strip()
                        self.friends.append(friend_zid)
                elif key == 'full_name':
                    self.full_name = val
                elif key == 'courses':
                    for course in val[1:-1].split(','):
                        course = course.strip()
                        self.courses.append(course)
                else:
                    self.info_dict[key] = val

    def insert_post(self, zid, time, message,longitude, latitude):
        self.posts.append(Post(zid, time, message, longitude, latitude,len(self.posts)))
        self.sorted_posts=sorted(self.posts,key=lambda x: x.time,reverse=True)

class Post:
    def __init__(self, zid, time, message, longitude, latitude, index):
        self.zid = zid
        self.time = time
        self.message = message
        self.index = index
        self.mention = re.findall(r'z[0-9]{7}',self.message,flags=re.IGNORECASE)
        # self.have_icon = False
        self.longitude = longitude
        self.latitude = latitude
        self.comments = []
        self.full_name=""
        self._name_init()

    # substitute zid plain text to href to page
    def show_message(self):
        out_text = re.sub(r'<', '&lt', self.message)
        out_text = re.sub(r'>', '&gt', out_text)
        out_text = re.sub(r'\\n', '<br />', out_text)
        out_text = re.sub(r'\n', '<br />', out_text)
        zids_sub = re.findall(r'z[0-9]{7}', out_text)
        for zid_sub in zids_sub:
            if zid_sub in user_object_dict:
                html = '<a target="_blank" href="{}">{}</a>'.format(url_for("profile_page", profile_zid=zid_sub),
                                                                    user_object_dict[zid_sub].full_name)
                # print(html)
                out_text = re.sub(zid_sub, html, out_text)
                # print(message_html)
            else:
                continue
        return out_text

    def _name_init(self):
        if self.zid not in zid_name_dict:
            with open(students_dir+'/'+self.zid+'/student.txt', encoding="utf8") as f:
                for line in f.readlines():
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()
                    if key == 'full_name':
                        self.full_name = val
                        zid_name_dict[self.zid] = self.full_name
        else:
            self.full_name=zid_name_dict[self.zid]


    def insert_comment(self, zid, time, message=""):
        self.comments.append(Comment(zid, time, message,len(self.comments)))


class Comment:
    def __init__(self, zid, time, message,index):
        self.zid = zid
        self.time = time
        self.message = message
        self.index = index
        self.mention = re.findall(r'z[0-9]{7}', self.message, flags=re.IGNORECASE)
        # if self.zid in check_icon:
        #     self.have_icon = True
        # else:
        #     self.have_icon = False
        self.replies = []
        self.full_name=""
        self._name_init()

    def _name_init(self):
        if self.zid not in zid_name_dict:
            with open(students_dir+'/'+self.zid+'/student.txt', encoding="utf8") as f:
                for line in f.readlines():
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()
                    if key == 'full_name':
                        self.full_name = val
                        zid_name_dict[self.zid]=self.full_name
        else:
            self.full_name=zid_name_dict[self.zid]

    def show_message(self):
        out_text = re.sub(r'<', '&lt', self.message)
        out_text = re.sub(r'>', '&gt', out_text)
        out_text = re.sub(r'\\n', '<br />', out_text)
        out_text = re.sub(r'\n', '<br />', out_text)
        zids_sub = re.findall(r'z[0-9]{7}', out_text)
        for zid_sub in zids_sub:
            if zid_sub in user_object_dict:
                html = '<a target="_blank" href="{}">{}</a>'.format(url_for("profile_page", profile_zid=zid_sub),user_object_dict[zid_sub].full_name)
                # print(html)
                out_text = re.sub(zid_sub, html, out_text)
                # print(message_html)
            else:
                continue
        return out_text

    def insert_reply(self, zid, time, message=""):
        self.replies.append(Reply(zid, time, message,len(self.replies)))


class Reply:
    def __init__(self, zid, time, message,index):
        self.zid = zid
        self.time = time
        self.message = message
        self.index = index
        self.mention = re.findall(r'z[0-9]{7}', self.message, flags=re.IGNORECASE)
        # if self.zid in check_icon:
        #     self.have_icon = True
        # else:
        #     self.have_icon = False
        self.full_name=""
        self._name_init()

    def show_message(self):
        out_text = re.sub(r'<', '&lt', self.message)
        out_text = re.sub(r'>', '&gt', out_text)
        out_text = re.sub(r'\\n', '<br />', out_text)
        out_text = re.sub(r'\n', '<br />', out_text)
        zids_sub = re.findall(r'z[0-9]{7}', out_text)
        for zid_sub in zids_sub:
            if zid_sub in user_object_dict:
                html = '<a target="_blank" href="{}">{}</a>'.format(url_for("profile_page", profile_zid=zid_sub),
                                                                    user_object_dict[zid_sub].full_name)
                # print(html)
                out_text = re.sub(zid_sub, html, out_text)
                # print(message_html)
            else:
                continue
        return out_text

    def _name_init(self):
        if self.zid not in zid_name_dict:
            with open(students_dir+'/'+self.zid+'/student.txt', encoding="utf8") as f:
                for line in f.readlines():
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()
                    if key == 'full_name':
                        self.full_name = val
                        zid_name_dict[self.zid] = self.full_name
        else:
            self.full_name=zid_name_dict[self.zid]



def postToFile(post):
    with open(os.path.join(students_dir,post.zid,"{}.txt".format(post.index)),'w', encoding="utf8") as f:
        print('message: {}'.format(post.message),file=f)
        print('from: {}'.format(post.zid), file=f)
        print('time: {}'.format(post.time), file=f)
        print('longitude: {}'.format(post.longitude), file=f)
        print('latitude: {}'.format(post.latitude), file=f)

def commentToFile(comment, post_i):
    with open(os.path.join(students_dir, post.zid, "{}-{}.txt".format(post_i,comment.index)), 'w', encoding="utf8") as f:
        print('message: {}'.format(comment.message), file=f)
        print('from: {}'.format(comment.zid), file=f)
        print('time: {}'.format(comment.time), file=f)

def replyToFile(reply, post_i, comment_i):
    with open(os.path.join(students_dir, post.zid, "{}-{}-{}.txt".format(post_i, comment_i,reply.index)), 'w', encoding="utf8") as f:
        print('message: {}'.format(reply.message), file=f)
        print('from: {}'.format(reply.zid), file=f)
        print('time: {}'.format(reply.time), file=f)


def dateToString(current_time=None):
    if current_time is None:
        current_time = datetime.now(timezone.utc)
    time_string = current_time.strftime("%Y-%m-%dT%H:%M:%S%z")

    return time_string

def send_email(to, subject, body):
    from_address = "z5128684@unsw.edu.au"
    to_address = to
    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address
    s = smtplib.SMTP('smtp.cse.unsw.edu.au')
    s.sendmail(from_address, [to_address], msg.as_string())
    s.quit()


def have_icon(zid):
    if os.path.isfile(students_dir + '/' + zid + '/img.jpg'):
        return True
    else:
        return False

def init_objects():
    for zid in os.listdir(students_dir):
        user=User(zid)
        user_object_dict[zid]=user
        user.read_post()

init_objects()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# @app.before_request
# def before_request():
#     g.user = None
#     if 'logged_in' in session:
#         g.user = user_object_dict[session['logged_in']]
#         if not g.user:
#             g.user = user_suspend_dict[session['logged_in']]

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'logged_in' in session:
        zid=session['logged_in']
        user=user_object_dict[zid]
        print(user_object_dict)
        return render_template('start.html',
                               key_hidden=key_hidden,
                               user=user,
                               user_dict=user_object_dict)
    else:
        return render_template('login.html',error='')



@app.route('/image/<path:filename>')
@login_required
def custom_static(filename):
    return send_from_directory(students_dir, filename)


@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    if request.form['message'] != '' and request.form['message'] is not None:
        zid = session['logged_in']
        post_message = request.form['message']
        post_privacy = request.form['post_privacy']
        current_time = dateToString()
        user=user_object_dict[zid]
        user.insert_post(zid,current_time,post_message,'','')
        post=user.posts[-1]
        postToFile(post)

        for zid_in_post in set(re.findall(r'z[0-9]{7}', post_message)):
            m_user = user_object_dict[zid_in_post]
            if m_user and m_user['email']:
                subj = "You are mentioned in {}'s post.".format(g.user['full_name'])
                path = url_for('search', _external=True)+'?suggestion={}'.format(zid_in_post)
                body = 'Check the link to check the post: <a href="{0}">{0}</a>'.format(path)
                send_email(m_user['email'], subj, body)

    return redirect(url_for('home'))


@app.route('/login', methods=['POST','GET'])
def login():
    zid = request.form.get('zid', '')
    password = request.form.get('password', '')
    # store zid in session cookie
    if zid in user_object_dict:
        user = user_object_dict[zid]
        if user.info_dict['password']==password:
            session['logged_in']=zid
            session['full_name']=user.full_name
            return redirect(url_for('home'))
    return render_template('login.html',error='Wrong zid and password combination!')

@app.route('/logout')
def logout():
    if 'logged_in' in session:
        session.pop('logged_in')
        session.pop('full_name')
    return render_template('login.html',error='')

@app.route('/zid/<profile_zid>', methods=['POST', 'GET'])
def profile_page(profile_zid):
    if 'logged_in' in session:
        friend=user_object_dict[profile_zid]
        return render_template('start.html',
                               key_hidden=key_hidden,
                               user=friend)
    else:
        return render_template('login.html',error='')

@app.route('/rpl/<path>', methods=['POST','GET'])
def reply(path):
    urls = path.split('a')
    post_zid = urls[0]
    zid = session['logged_in']
    post_message = request.form['message']
    post_privacy = request.form['post_privacy']
    if request.form['message'] != '' and request.form['message'] is not None:
        if len(urls)>2:
            return redirect(url_for('home'))
        else:
            current_time = dateToString()
            if len(urls) == 3:
                post_id = urls[1]
                comment_id=urls[2]
                post_owner=user_object_dict[post_zid]
                comment=post_owner.posts[post_id].comments[comment_id]
                comment.insert_reply(zid, current_time, post_message)
                reply = comment.replies[-1]
                replyToFile(reply,post_id,comment_id)

            elif len(urls) == 2:
                post_id = urls[1]
                post_owner = user_object_dict[post_zid]
                post=post_owner.posts[post_id]
                post.insert_comment(zid,current_time,post_message,'','')
                comment=post.comments[-1]
                commentToFile(comment,post_id)

            return redirect(url_for('home'))
    else:
        if len(urls) == 3:
            post_id = urls[1]
            comment_id = urls[2]
            post_owner = user_object_dict[post_zid]
            comment = post_owner.posts[post_id].comments[comment_id]
            return render_template('reply.html', user=g.user, post=comment)
        elif len(urls) == 2:
            post_id = urls[1]
            post_owner = user_object_dict[post_zid]
            post = post_owner.posts[post_id]
            return render_template('reply.html', user=g.user, post=post)


if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(host="127.0.0.3", port=5000,debug=True)
