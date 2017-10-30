#!/usr/bin/python3.6

import os, re, sys
import sqlite3
import shutil
from collections import defaultdict


def constant_factory(value):
    return lambda: value


def read_users_info(users, data_dir):
    users_info_list = []
    img_dir = os.path.join('static', 'profile_img')
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)
    for user in users:
        info_dict = defaultdict(constant_factory('null'))
        details_filename = os.path.join(data_dir, user, "student.txt")
        old_img_path = os.path.join(data_dir, user, "img.jpg")
        new_img_dir = os.path.join('static', 'profile_img', user)
        if not os.path.exists(new_img_dir):
            os.mkdir(new_img_dir)
        with open(details_filename, encoding="utf8") as f:
            details = f.readlines()
            for line in details:
                key, val = line.split(':', 1)
                key = key.strip()
                val = val.strip()
                if key == 'courses' or key == 'friends':
                    val_list = re.findall(r'[^(,) ]+', val)
                    info_dict[key] = val_list
                else:
                    info_dict[key] = val
        if os.path.exists(old_img_path):
            info_dict['img_exist'] = 1
            shutil.copy('{}/{}/img.jpg'.format(data_dir,user), 'static/profile_img/{}'.format(user))
            # os.system('cp {0}/{1}/img.jpg static/profile_img/{1}'.format(data_dir,user))
        else:
            info_dict['img_exist'] = 0
        users_info_list.append(info_dict)
    return users_info_list


def read_posts(users, data_dir):
    user_posts = []
    for user in users:
        i = 0
        posts = []
        post_path = os.path.join(data_dir, user, '{}.txt'.format(i))
        while os.path.isfile(post_path):
            post_dict = defaultdict(constant_factory('null'))
            with open(post_path, encoding="utf8") as f:
                for line in f.readlines():
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()

                    if key == 'message':
                        r = '<br />'
                        val = val.replace('\\n', r)
                    post_dict[key] = val

            j = 0
            comment_path = os.path.join(data_dir, user, '{}-{}.txt'.format(i, j))
            comments = []
            while os.path.isfile(comment_path):
                comment_dict = defaultdict(constant_factory('null'))
                with open(comment_path, encoding="utf8") as f:
                    for line in f.readlines():
                        key, val = line.split(':', 1)
                        key = key.strip()
                        val = val.strip()
                        if key == 'message':
                            r = '<br />'
                            val = val.replace('\\n', r)
                        comment_dict[key] = val

                k = 0
                reply_path = os.path.join(data_dir, user, '{}-{}-{}.txt'.format(i, j, k))
                replies = []
                while os.path.isfile(reply_path):
                    reply_dict = defaultdict(constant_factory('null'))
                    with open(reply_path, encoding="utf8") as f:
                        for line in f.readlines():
                            key, val = line.split(':', 1)
                            key = key.strip()
                            val = val.strip()
                            if key == 'message':
                                r = '<br />'
                                val = val.replace('\\n', r)
                            reply_dict[key] = val
                    replies.append(reply_dict)
                    k += 1
                    reply_path = os.path.join(data_dir, user, '{}-{}-{}.txt'.format(i, j, k))

                comments.append([comment_dict, replies])
                j += 1
                comment_path = os.path.join(data_dir, user, '{}-{}.txt'.format(i, j))

            posts.append([post_dict, comments])
            i += 1
            post_path = os.path.join(data_dir, user, '{}.txt'.format(i))
        user_posts.append(posts)
    return user_posts


schema_path = "/database/schema.sql"

if __name__ == '__main__':
    data_dir = sys.argv[1]
    # data_dir = 'dataset-small'
    db_file = 'database/{}.db'.format(data_dir)
    if not os.path.isdir(data_dir):
        print('data_dir not exists')
        exit(1)
    if not os.path.isdir('database'):
        os.mkdir('database')
    users = os.listdir(data_dir)
    users_info_list = read_users_info(users, data_dir)
    print(' User attributes in dict ')
    os.system("sqlite3 {} < schema.sql".format(db_file))
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    users_insert = []
    for info_dict in users_info_list:
        users_insert.append((info_dict['zid'],
                             info_dict['password'],
                             info_dict['full_name'],
                             info_dict['email'],
                             info_dict['birthday'],
                             info_dict['img_exist'],
                             info_dict['program'],
                             info_dict['home_suburb'],
                             info_dict['home_longitude'],
                             info_dict['home_latitude']))
    insert_sql = "INSERT INTO user VALUES (?,?,?,?,?,?,?,?,?,?,'',1)"
    result = cur.executemany(insert_sql, users_insert)
    print("{} users inserted.".format(len(users_insert)))

    for user_dict in users_info_list:
        for friend in user_dict['friends']:
            cur.execute("DELETE FROM friends WHERE user_zid=? AND friend_zid=?",
                        [friend, user_dict['zid']])
            cur.execute("DELETE FROM friends WHERE user_zid=? AND friend_zid=?",
                        [user_dict['zid'], friend])
            insert_friend_sql = "INSERT INTO friends(user_zid, friend_zid, confirmed) VALUES (?, ?, ?)"
            cur.executemany(insert_friend_sql, [(user_dict['zid'], friend, 1)])
            insert_friend_sql = "INSERT INTO friends(user_zid, friend_zid, confirmed) VALUES (?, ?, ?)"
            cur.executemany(insert_friend_sql, [(friend, user_dict['zid'], 1)])
        for course in user_dict['courses']:
            insert_course_sql = "INSERT INTO enrollment(zid, course) VALUES (?, ?)"
            cur.executemany(insert_course_sql, [(user_dict['zid'], course)])
    user_posts_list = read_posts(users, data_dir)
    post_id = 0
    comment_id = 0
    reply_id = 0
    for user_posts in user_posts_list:
        for post_dict, comments in user_posts:
            insert_post_sql = "INSERT INTO post(id, zid, time, latitude, longitude, message, privacy) VALUES (?, ?, ?, ?, ?, ?, 'public')"
            post_id += 1
            cur.execute(insert_post_sql,
                        [post_id, post_dict["from"], post_dict["time"], post_dict["message"], post_dict["latitude"],post_dict["longitude"]])
            for comment_dict, replies in comments:
                insert_comment_sql = "INSERT INTO comment(id, post_id, zid, time, message) VALUES (?, ?, ?, ?, ?)"
                comment_id += 1
                cur.execute(insert_comment_sql,
                            [comment_id, post_id, comment_dict['from'], comment_dict['time'], comment_dict['message']])
                for reply_dict in replies:
                    insert_reply_sql = "INSERT INTO reply(id, comment_id, zid, time, message) VALUES (?, ?, ?, ?, ?)"
                    reply_id += 1
                    cur.execute(insert_reply_sql,
                                [reply_id, comment_id, reply_dict['from'], reply_dict['time'], reply_dict['message']])

    conn.commit()
    conn.close()