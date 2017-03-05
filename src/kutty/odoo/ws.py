import ConfigParser
import thread

import util
from flask import jsonify

import activity
from ..ws.main import *


class OdooWS(Main):
    def __init__(self):
        kutty_config = ConfigParser.ConfigParser()
        cnf_filename = util.configuration.find_config_file()
        print cnf_filename
        kutty_config.read(cnf_filename)
        kutty_config = kutty_config._sections
        self.activity = activity.OdooInstanceActivity(kutty_config)

    @route('/odoo/instance/', methods=["GET", "POST", "PUT"])
    @requires_auth
    def instance(self):
        if request.method == 'POST':
            if request.headers.get('Content-Type') == 'application/json':
                project_name = request.json['project']['name']
                if self.activity.has_project_exits(project_name):
                    return 'Project %s already exits' % project_name, 400
                thread.start_new_thread(self.activity.install, (request.json,))
                return "done"
            else:
                return 'Only json Content-type is allowed', 400
        elif request.method == 'PUT':
            if request.headers.get('Content-Type') == 'application/json':
                action = request.json.get('action', None)
                try:
                    if action == 'stopall':
                        self.activity.stop_all()
                    elif action == 'startall':
                        self.activity.start_all()
                    else:
                        return 'Invalid action command', 400
                except activity.OAException as ex:
                    return ex.message, 400
            else:
                return 'Only json Content-type is allowed', 400
        return jsonify(self.activity.list_instance())

    @route('/odoo/instance/<name>/', methods=["GET", "PUT"])
    @requires_auth
    def get_instance_info(self, name):
        if request.method == 'PUT':
            action = request.json.get('action', None)
            try:
                if action == 'stop':
                    thread.start_new_thread(self.activity.stop, (name,))
                elif action == 'start':
                    thread.start_new_thread(self.activity.start, (name,))
                elif action == 'restart':
                    self.activity.restart(name)
                elif action == 'sendlog':
                    auth = request.authorization
                    usrmng_activity = UserManagementActivity()
                    email = usrmng_activity.get_user(auth.username)['email']
                    self.activity.send_log(name, email)
                elif action == 'upgrade':
                    self.activity.upgrade(name)
                elif action == 'upgradesrc':
                    self.activity.upgradesrc(name)
                elif action == 'updatedb':
                    self.activity.updatedb(name)
                else:
                    return 'Invalid action command', 400

            except activity.OAException as ex:
                return ex.message, 400

        return jsonify(self.activity.get_instance_info(name))

    @route('/odoo/instance/<name>/', methods=["DELETE"])
    @requires_auth
    def delete_instance(self, name):
        try:
            self.activity.remove(name)
        except activity.OAException as ex:
            return ex.message, 400
        return "done"
