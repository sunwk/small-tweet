# coding:utf-8

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import sql

import time
import shutil
import hashlib




# 数据库的路径
db_path = 'db.sqlite'
# 获取 app 的实例
app = Flask(__name__)
# 这个先不管，其实是 flask 用来加密 session 的东西
app.secret_key = 'random string'
# 配置数据库的打开方式
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(db_path)

db = SQLAlchemy(app)


def sha1_hashed(s):
    encoding = 'utf-8'
    return hashlib.sha1(s.encode(encoding)).hexdigest()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), unique=True)
    password = db.Column(db.String())
    role = db.Column(db.Integer, default=2)
    signature = db.Column(db.String())
    visit = db.Column(db.Integer)
    sex = db.Column(db.String())

    tweets = db.relationship('Tweet', backref='user')
    comments = db.relationship('Comment', backref='user')

    def __init__(self, form):
        super(User, self).__init__()
        self.visit = int(0)
        self.username = form.get('username', '')
        self.password = sha1_hashed(form.get('password', ''))
        self.signature = form.get('signature', '')
        self.sex = form.get('sex', '')

    def __repr__(self):
        class_name = self.__class__.__name__
        return u'<{}:{}>'.format(class_name, self.id)

    def visitors_add(self):
        self.visit += 1

    def is_admin(self):
        return self.role == 1

    def valid(self):
        is_username = len(self.username) >= 3
        is_password = len(self.password) >= 3
        return is_username and is_password

    def validate(self, user):
        username_equals = self.username == user.username
        password_equals = self.password == user.password
        if isinstance(user, User):
            return username_equals and password_equals
        else:
            return False

    def save(self):
        db.session.add(self)
        db.session.commit()


class Tweet(db.Model):
    __tablename__ = 'tweets'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String())
    created_time = db.Column(db.DateTime(timezone=True), default=sql.func.now())

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='tweet')

    def __init__(self, form):
        super(Tweet, self).__init__()
        self.content = form.get('content', '')

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String())
    created_time = db.Column(db.DateTime(timezone=True), default=sql.func.now())

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweets.id'))

    def __init__(self, form):
        super(Comment, self).__init__()
        self.content = form.get('content', '')

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


def backup_db():
    backup_path = '{}.{}'.format(time.time(), db_path)
    shutil.copyfile(db_path, backup_path)


# 定义了数据库，如何创建数据库呢？
# 调用 db.create_all()
# 如果数据库文件已经存在了，则啥也不做
# 所以说我们先 drop_all 删除所有表
# 再重新 create_all 创建所有表
def rebuild_db():
    backup_db()
    db.drop_all()
    db.create_all()
    print('rebuild database')


# 第一次运行工程的时候没有数据库
# 所以我们运行 models.py 创建一个新的数据库文件
if __name__ == '__main__':
    rebuild_db()