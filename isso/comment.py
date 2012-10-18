# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

from werkzeug.wrappers import Response
from werkzeug.exceptions import abort

from itsdangerous import SignatureExpired, BadSignature

from isso import json, models


def create(app, environ, request, path):

    try:
        rv = app.db.add(path, models.Comment.fromjson(request.data))
    except ValueError as e:
        return Response(unicode(e), 400)

    response = Response(json.dumps(rv), 201, content_type='application/json')
    response.set_cookie('session', app.signer.dumps([path, rv.id]), max_age=app.MAX_AGE)
    return response


def get(app, environ, request, path, id=None):

    rv = list(app.db.retrieve(path)) if id is None else app.db.get(path, id)
    if not rv:
        abort(404)
    return Response(json.dumps(rv), 200, content_type='application/json')


def modify(app, environ, request, path, id):

    try:
        rv = app.unsign(request.cookies.get('session', ''))
    except (SignatureExpired, BadSignature):
        return abort(403)

    if not (rv[0] == '*' or rv == [path, id]):
        abort(401)

    if request.method == 'PUT':
        try:
            rv = app.db.update(path, id, models.Comment.fromjson(request.data))
        except ValueError as e:
            return Response(unicode(e), 400)
    else:
        rv = app.db.delete(path, id)
    return Response(json.dumps(rv), 200, content_type='application/json')