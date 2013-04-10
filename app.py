#!/usr/bin/python
# encoding: UTF-8

import config
import logging

from models import init_db
from query.topic import topic_notify
from query.account import get_current_user
from utils.ua import check_ua, render_template

#from views.mail import mail
from views.oauth import oauth
from views.topic import topic
from views.people import people
from views.account import account

from utils.weixin import Message, compute_signature, \
        return_message, check_code

from sheep.api.statics import static_files, \
        upload_files
from sheep.api.sessions import SessionMiddleware, \
    FilesystemSessionStore

from flaskext.csrf import csrf
from flask import Flask, request, g, abort

app = Flask(__name__)
app.debug = config.DEBUG
app.secret_key = config.SECRET_KEY
app.jinja_env.filters['s_files'] = static_files
app.jinja_env.filters['u_files'] = upload_files

app.config.update(
    SQLALCHEMY_DATABASE_URI = config.DATABASE_URI,
    SQLALCHEMY_POOL_SIZE = 100,
    SQLALCHEMY_POOL_TIMEOUT = 10,
    SQLALCHEMY_POOL_RECYCLE = 3600,
    SESSION_COOKIE_DOMAIN = config.SESSION_COOKIE_DOMAIN,
    MAX_CONTENT_LENGTH = config.MAX_CONTENT_LENGTH,
)

oauth.register_blueprints(app)
app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(people, url_prefix='/people')
app.register_blueprint(topic, url_prefix='/mail')
#app.register_blueprint(mail, url_prefix='/mail')

logger = logging.getLogger(__name__)

init_db(app)
csrf(app)
app.wsgi_app = SessionMiddleware(app.wsgi_app, \
        FilesystemSessionStore(), \
        cookie_name=config.SESSION_KEY, cookie_path='/', \
        cookie_domain=config.SESSION_COOKIE_DOMAIN)

@app.route('/')
@check_ua
def index():
    return render_template('index.html')

@app.route('/wx/', methods=["GET"])
def check_valid():
    args = dict(request.args.items())
    check_keys(args, ["signature", "timestamp", "nonce", "echostr"])
    signature = compute_signature(args.copy())
    if signature != args['signature']:
        logging.warning("Sigature error. %s", signature)
        raise abort(400)
    return args['echostr']

@app.route('/wx/', methods=["POST"])
def receive_msg():
    msg = Message(request.data)
    msg_splited = msg.Body.split(" ")
    if msg_splited[0] == "-code":
        if len(msg_splited) == 2:
            return return_message(msg.To, msg.From, check_code(msg_splited[1]))
        else:
            return return_message(msg.To, msg.From, "绑定失败，请检查验证码格式。")
    return ""

@app.before_request
def before_request():
    g.session = request.environ['xiaomen.session']
    g.current_user = get_current_user()
    #TODO remove
    if g.current_user:
        g.topic_notify = lambda: topic_notify(g.current_user.id)

