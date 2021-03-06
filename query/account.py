#!/usr/local/bin/python2.7
#coding:utf-8

from flask import g
from sheep.api.cache import cache
from utils.validators import check_domain
from models.account import User, Forget, OAuth
from sheep.api.cache import backend, cross_cache

@cache('account:{username}', 86400)
def get_user(username):
    try:
        username = int(username)
        if username <= 0:
            return None
        return User.query.get(username)
    except ValueError:
        if check_domain(username):
            return None
        return get_user_by_domain(domain=username)

@cache('account:{domain}', 86400)
def get_user_by_domain(domain):
    return get_user_by(domain=domain).limit(1).first()

@cache('account:{email}', 86400)
def get_user_by_email(email):
    return get_user_by(email=email).limit(1).first()

@cache('account:{weixin}', 86400)
def get_user_by_weixin(weixin):
    return get_user_by(weixin=weixin).limit(1).first()

@cache('account:{stub}', 300)
def get_forget_by_stub(stub):
    return Forget.query.filter_by(stub=stub).first()

def get_oauth_by(**kw):
    return OAuth.query.filter_by(**kw).first()

def get_user_by(**kw):
    return User.query.filter_by(**kw)

def get_current_user():
    if not g.session or not g.session.get('user_id') or not g.session.get('user_token'):
        return None
    user = get_user(g.session['user_id'])
    if g.session['user_token'] != user.token:
        return None
    return user

def clear_user_cache(user):
    keys = ['account:%s' % key for key in [str(user.id), user.domain, user.email]]
    backend.delete_many(*keys)
    cross_cache.delete('open:account:info:{0}'.format(user.id))

create_forget = Forget.create
create_user = User.create

