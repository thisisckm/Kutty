from functools import wraps

from flask import request, Response
from flask_classy import FlaskView, route

from ..usrmng.activity import UserManagementActivity, UserCredential, UMException
from ..system.activity import SystemActivity


def check_auth(username, password):
    try:
        print username, password
        userManagementActivity = UserManagementActivity()
        return userManagementActivity.check_authentication(UserCredential(username, password))
    except UMException as ex:
        return False


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


class Main(FlaskView):
    route_base = '/api/'

    @route('/')
    def index(self):
        return "Hello,\n I am Kutty"

    @route('/healthcheck', methods=['GET'])
    def health_check(self):
        sa = SystemActivity()
        if sa.healtcheck():
            return "Kutty's health is 100% ok", 200
        return "Kutty's health is worrying", 418
