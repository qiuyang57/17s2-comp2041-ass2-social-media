-- write by Yang Qiu for COMP9041 at 10/30/2017
-- Unswtalk schema
DROP TABLE IF EXISTS user;
CREATE TABLE user (
  'zid'            TEXT PRIMARY KEY NOT NULL,
  'password'       TEXT             NOT NULL,
  'full_name'      TEXT,
  'email'          TEXT,
  'birthday'       TEXT,
  'img_exist'      INTEGER,
  'program'        TEXT,
  'home_suburb'    TEXT,
  'home_longitude' TEXT,
  'home_latitude'  TEXT,
  'profile_text'   TEXT,
  'confirmed'      INTEGER
);

DROP TABLE IF EXISTS user_suspend;
CREATE TABLE user_suspend AS
  SELECT *
  FROM user;

DROP TABLE IF EXISTS user_to_confirm;
CREATE TABLE user_to_confirm AS
  SELECT *
  FROM user;


DROP TABLE IF EXISTS friends;
CREATE TABLE friends (
  id         INTEGER PRIMARY KEY   AUTOINCREMENT,
  user_zid   TEXT REFERENCES user (zid),
  friend_zid TEXT,
  confirmed  INTEGER
);

DROP TABLE IF EXISTS enrollment;
CREATE TABLE enrollment
(
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  zid    TEXT REFERENCES user (zid),
  course TEXT
);


DROP TABLE IF EXISTS post;
CREATE TABLE post
(
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  zid       TEXT REFERENCES user (zid),
  time      TEXT,
  message   TEXT,
  latitude  TEXT,
  longitude TEXT,
  privacy   TEXT
);

DROP TABLE IF EXISTS comment;
CREATE TABLE comment
(
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER REFERENCES post (id),
  zid     TEXT REFERENCES user (zid),
  time    TEXT,
  message TEXT
);

DROP TABLE IF EXISTS reply;
CREATE TABLE reply
(
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  comment_id INTEGER REFERENCES comment (id),
  zid        TEXT REFERENCES user (zid),
  time       TEXT,
  message    TEXT
);