from OpenSSL import SSL

from flask import Flask
from util import configuration

from daemon import Daemon
from odoo.ws import OdooWS
from usrmng.ws import UserManagementWS


class KuttyWS(Daemon):
    def __init__(self):
        stdout, stderr = configuration.find_log_files()
        home_dir = configuration.get_home_path()
        pidfile = '%s/kutty.pid' % home_dir
        super(KuttyWS, self).__init__(pidfile, stdout=stdout, stderr=stderr)

    def run(self):
        app = Flask(__name__)
        OdooWS.register(app)
        UserManagementWS.register(app)
        context = SSL.Context(SSL.SSLv23_METHOD)
        key_file, cert_file = configuration.find_cert_files()
        context = (cert_file, key_file)
        app.run(host='0.0.0.0', port=9090, ssl_context=context)

    def start_ws_server(self):
        self.start()

    def stop_ws_server(self):
        self.stop()
