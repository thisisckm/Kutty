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

    @route('/usrmng/user/<user>/', methods=["GET"])
    @requires_auth
    def get_user(self, user):
        return jsonify(self.activity.get_user(user))
