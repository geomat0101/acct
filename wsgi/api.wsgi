#!/bin/env python

import cgi
import json
import sys
import urlparse

from Cookie import SimpleCookie
from decimal import Decimal as D
from tempfile import TemporaryFile

sys.path.insert(0, "/home/mdg/src")

from acct.api import api as API
from acct.acct import Account


def load_acctlist (db, loggedIn):
    total_debits  = D(0)
    total_credits = D(0)

    accts = db.get_acctlist()

    acctlist = []

    for (t, a) in accts:
        curracct = Account(db, a, t)
        if curracct.debit_balance != "": 
            total_debits  += D(curracct.debit_balance)
        if curracct.credit_balance != "": 
            total_credits += D(curracct.credit_balance)
        acctlist.append([t, a, str(curracct.debit_balance), str(curracct.credit_balance)])

    return {'logged_in': loggedIn, 'total_debits': str(total_debits), 'total_credits': str(total_credits), 'acctlist': acctlist}


def application(environ, start_response):
    status = '200 OK'
    query = urlparse.parse_qs(environ['QUERY_STRING'])
    response_headers = [('Content-type', 'text/plain')]

    cookies = SimpleCookie()
    cookies.load(environ.get("HTTP_COOKIE",""))

    # check cookies for an active session
    sessionId = None
    if 'sessionId' in cookies:
        sessionId = cookies['sessionId'].value

    # if username and password are supplied then reauthenticate
    username = password = None
    if 'username' in query and 'password' in query:
        username = query['username'][0]
        password = query['password'][0]

    api = API(sessionId, username=username, password=password)

    # quick and dirty wsgi-rpc... assume caller knows what they're doing
    method = query['method'][0]

    if method == 'logout':
        api.sid = 'LOGOUT'

    if api.sid != sessionId:
        sessionId = api.sid
        session_cookie = SimpleCookie()
        session_cookie['sessionId'] = api.sid
        session_cookie['sessionId']["Path"] = '/'

        for morsel in session_cookie.values():
            response_headers.extend([("set-cookie", morsel.OutputString())])

    if method == 'auth':
        res = False
        if api.userAuth:
            res = "Login Successful"
    elif method == 'logout':
        res = 'Logged out'
    elif method == 'load_acctlist':
        res = load_acctlist(api.db, api.loggedIn)
    elif method == 'upload':
        formdata = cgi.FieldStorage(environ=environ, fp=environ['wsgi.input'])
        if 'newfile' in formdata and formdata['newfile'].filename != '':
            with TemporaryFile(mode='w+b') as body:
                body.write(formdata['newfile'].file.read())
                body.seek(0)

                api.applyQIFData(formdata['acctType'].value, formdata['acctName'].value, body)

        start_response('301 Redirect', [('Location', '/#/import'),])
        return []
    else:
        try:
            args = query['args']
        except KeyError:
            args = []

        res = getattr(api, method).__call__(*args)

    start_response(status, response_headers)
    return [json.dumps(res, indent=2)]

# :vim set syntax=python
