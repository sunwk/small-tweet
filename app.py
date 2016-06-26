# coding:utf-8

from flask import Flask
from flask import render_template
from flask import redirect
from flask import url_for
from flask import request
from flask import make_response
from flask import abort
from flask import flash
from flask import session

import uuid
import time

from models import User
from models import Comment
from models import Tweet





app = Flask(__name__)
app.secret_key = 'lxx'
cookie_dict = {}

def current_user():
    # cid = request.cookies.get('cookie_id', '')
    # user = cookie_dict.get(cid, None)
    user_id = session['user_id']
    user = User.query.filter_by(id=user_id).first()
    return user


def log(*args):
    t = time.time()
    tt =  time.strftime(r'%Y/%m/%d %H:%M:%S', time.localtime(t))
    print(tt, *args)
    with open('log.txt', 'a') as f:
        f.write('{} : {}\n'.format(tt, *args))
        f.close()


@app.route('/')
def root_view():
    return redirect(url_for('login_view'))


@app.route('/login')
def login_view():
    return render_template('login.html')

# 因为登录和注册页面时在一起的，所以这个视图函数其实没有必要
@app.route('/register')
def register_view():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    u = User(request.form)
    user = User.query.filter_by(username=u.username).first()
    if user is not None:
        if user.validate(u):
            log('用户登录成功', user,user.username,user.password)
            # cookie_id = str(uuid.uuid4())
            # cookie_dict[cookie_id] = user
            session['user_id'] = user.id
            r = redirect(url_for('tweet_view', user_id=user.id))
            # r.set_cookie('cookie_id', cookie_id)
            return r
        else:
            flash('账号名或密码错误，需重新登录')
            log('账号名或密码错误，需重新登录', user)
            return redirect(url_for('login_view'))
    else:
        flash('用户尚未注册，须先注册再登录')
        log('用户尚未注册，须先注册再登录', user)
        return redirect(url_for('register_view'))


@app.route('/register', methods=['POST'])
def register():
    u = User(request.form)
    if u.valid():
        log('注册成功，已跳转到内容页面')
        u.save()
        return redirect(url_for('login_view'))
    else:
        flash('用户名或密码不合规范，需重新输入')
        log('用户名或密码不合规范，需重新输入')
        return redirect(url_for('register_view'))


@app.route('/tweet/<user_id>')
def tweet_view(user_id):
    user = User.query.filter_by(id=user_id).first()
    u = current_user()
    log('debug current_user is:',u)
    if user is not None:
        user.visitors_add()
        if u is not None:
            if user.is_admin():
                tweets = Tweet.query.all()
                return render_template('tweet.html', user=user, tweets=tweets)
            else:
                tweets = user.tweets
                tweets.sort(key=lambda t: t.created_time, reverse=True)
                users = User.query.all()
                user_others = []
                for user in users:
                    if user.id == u.id:
                        user_self = user
                    else:
                        user_others.append(user)
                return render_template('tweet.html', user=user_self, users=user_others, tweets=tweets)
        else:
            return redirect(url_for('login_view'))
    else:
        abort(404)


@app.route('/tweet/add/<user_id>', methods=['POST'])
def tweet_add(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user is not None:
        log('有这个人注册过')
        u = current_user()
        log('debug current_user:',u)
        if u is not None and u.id == user.id:
            log('当前有人登陆且登陆的人是这个人')
            tweet = Tweet(request.form)
            tweet.user = u
            tweet.save()
            return redirect(url_for('tweet_view', user_id=u.id))
        else:
            return redirect(url_for('login_view'))
    else:
        abort(404)


@app.route('/tweet/update/<tweet_id>')
def tweet_update_view(tweet_id):
    tweet = Tweet.query.filter_by(id=tweet_id).first()
    if tweet is None:
        abort(404)
    else:
        user = current_user()
        if user is None or user.id != tweet.user_id:
            abort(401)
        else:
            print('debug  user.id:', user.id, 'debug thing.user_id:', tweet.user_id)
            # 这里出bug了，蛋疼，总是返回401或者404
            # return redirect(render_template('thing_edit.html', thing=thing))
            return render_template('tweet_edit.html', tweet=tweet)


@app.route('/tweet/update/<tweet_id>', methods=['POST'])
def tweet_update(tweet_id):
    print('debug tweet_id:', tweet_id)
    tweet = Tweet.query.filter_by(id=tweet_id).first()
    print('debug thin:', tweet)
    if tweet is None:
        abort(404)
    else:
        user = current_user()
        if user is None or user.id != tweet.user_id:
            abort(401)
        else:
            tweet.content = request.form.get('content', '')
            tweet.save()
            return redirect(url_for('tweet_view', user_id=user.id))


@app.route('/tweet/delete/<tweet_id>')
def tweet_delete(tweet_id):
    print('debug thing_id:', tweet_id)
    tweet = Tweet.query.filter_by(id=tweet_id).first()
    print('debug thin:', tweet)
    if tweet is None:
        abort(404)
    else:
        user = current_user()
        if user is None or user.id != tweet.user_id:
            abort(401)
        else:
            tweet.delete()
            return redirect(url_for('tweet_view', user_id=user.id))


# 感叹：user_id是信息的中枢，你要能根据这个user_id为线头，把你想要在页面里展示的数据全部找出来。至于能不能找到，怎么找，和怎么样找起来快，就要看数据库的表之间的结构如何设计。
@app.route('/tweet/others/<user_id>')
def other_tweet_view(user_id):
    # 从tweet页面链过来的user_id,指的是作为当前登陆者的你想看其微博的那个人的user_id,这一步是找到这个人
    user = User.query.filter_by(id=user_id).first()
    # 这是找到当前登录者
    u = current_user()
    # 根据comments表的外键user_id找到想看的这个人的所有评论   错了.....
    # comments = Comment.query.filter_by(user_id=user_id)
    if user is not None:
        user.visitors_add()
        if u is not None:
            # tweets = user.tweets
            return render_template('tweet_others.html', user=user)
        else:
            return redirect(url_for('login_view'))
    else:
        abort(404)


# 感悟:GET方法对应的视图函数只需要从数据库里拿出对应的东西发回去就好，这些数据怎么装进数据库是POST的事情
@app.route('/comment/tweet/<tweet_id>')
def tweet_comment_view(tweet_id):
    # 通过外键tweet_id找到这条tweet对应的comment们
    tweet = Tweet.query.filter_by(id=tweet_id).first()
    # 这一步是他妈的啥，这都哪跟哪，本意是好的，想根据评论对象的这个tweet的tweet_id拿到这个tweet下对应的所有评论，但是comment的id和tweet_id有鸡毛关系
    # 要是能从众多comment中挑出tweet_id == 指定的tweet_id的comment，那倒也挺好，但问题是做不到。
    # comments = Comment.query.filter_by(id=tweet_id)

    # 加个relationship直接tweet.comments拿到就好，我终于把relationship的用法彻底搞明白了
    u = current_user()
    if u is not None:
        comment = []
        # for c in comments:
        #     if c.user_id == u.id:
        #         comment.append(c)
        return render_template('tweet_comment.html', comments=tweet.comments, tweet=tweet)
    else:
        return redirect(url_for('login_view'))


@app.route('/comment/add/<tweet_id>', methods=['POST'])
def tweet_comment(tweet_id):
    user = current_user()
    if user is not None:
        comment = Comment(request.form)
        comment.tweet_id = tweet_id
        comment.user_id = user.id
        comment.save()
        return redirect(url_for('tweet_comment_view', tweet_id=tweet_id))
    else:
        return redirect(url_for('login_view'))
# @app.route('/admin/users')
# def admin_view

if __name__ == '__main__':
    # host, port = '0.0.0.0', 15000
    # args = {
    #     'host': host,
    #     'port': port,
    #     'debug': True,
    # }
    # app.run(**args)
    app.run(debug=True)