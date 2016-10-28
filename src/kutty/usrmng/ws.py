from flask import jsonify

import activity
from ..ws.main import *


class UserManagementWS(Main):
    def __init__(self):
        self.activity = activity.UserManagementActivity()

    @route('/usrmng/user/', methods=["GET"])
    @requires_auth
    def user(self):
        return jsonify(self.activity.listuser())

    @route('/usrmng/user/<username>/', methods=["GET"])
    @requires_auth
    def get_user(self, username):
        return jsonify(self.activity.get_user(username))

    @route('/usrmng/user/<username>/', methods=["PUT"])
    @requires_auth
    def update_user(self, username):
        if request.headers.get('Content-Type') == 'application/json':
            name = request.json.get('name', None)
            email = request.json.get('email', None)
            password = request.json.get('password', None)
            image = request.json.get('image', None)

            try:
                self.activity.updateuser(username, name, email, password, image)
            except UMException:
                return 'Username %s is not exits' % username, 400
            return "done"
        else:
            return 'Only json Content-type is allowed', 400
