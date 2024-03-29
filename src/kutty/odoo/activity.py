import os
import os.path
import shutil
import smtplib
import subprocess
import tempfile
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

import psutil
import psycopg2

from ..activity import Activity


class OdooInstanceActivity(Activity):
    def _check_instances(self):
        result_set = self.odoo_instances.find({"status": "Running"}, {'_id': 0}).sort("port_no", 1)
        for elm in result_set:
            self._refresh_server_status(elm['name'])

    def __init__(self, kutty_config):
        Activity.__init__(self)
        self.kutty_config = kutty_config
        self.projects_home = kutty_config['general']['project_home']
        self.pid_file = '.pid'
        user_home = os.path.expanduser('~')
        self.dot_kutty_path = '%s/.kutty' % user_home

        if not os.path.exists(self.projects_home):
            try:
                os.mkdir(self.projects_home)
            except OSError:
                print "No such directory"
                exit(1)

        self._first_deploy()
        self._check_instances()

    def _update_apache_config(self, server_name, portno):
        template = "<VirtualHost *:80>\n"
        template = template + "ServerName %s\n"
        template = template + "ProxyPass / http://localhost:%s/\n"
        template = template + "ProxyPassReverse / http://localhost:%s/\n"
        template = template + "</VirtualHost>"

        output = template % (server_name, portno, portno)
        temp_file = tempfile.gettempdir() + os.path.sep + server_name
        conf_file = "%s%s%s.conf" % (self.kutty_config['apache']['sa_path'], os.path.sep, server_name)
        link_file = "%s%s%s.conf" % (self.kutty_config['apache']['se_path'], os.path.sep, server_name)

        ostream = open(temp_file, 'w')
        ostream.write(output)
        ostream.flush()
        ostream.close()

        command = ['sudo', 'cp', temp_file, conf_file]
        subprocess.Popen(command, stdin=subprocess.PIPE)
        command = ['sudo', 'ln', '-s', conf_file, link_file]
        subprocess.Popen(command, stdin=subprocess.PIPE)
        command = ['sudo', 'apachectl', '-k', 'graceful']
        subprocess.Popen(command, stdin=subprocess.PIPE)

    def _remove_apache_config(self, server_name):
        conf_file = "%s%s%s.conf" % (self.kutty_config['apache']['sa_path'], os.path.sep, server_name)
        link_file = "%s%s%s.conf" % (self.kutty_config['apache']['se_path'], os.path.sep, server_name)
        command = ['sudo', 'rm', conf_file, link_file]
        subprocess.Popen(command, stdin=subprocess.PIPE)
        command = ['sudo', 'apachectl', '-k', 'graceful']
        subprocess.Popen(command, stdin=subprocess.PIPE)

    def _startup_file_location(self):
        if not os.path.isdir('setup'):
            if os.path.isfile('odoo/openerp-server'):
                return 'odoo/openerp-server'
            elif os.path.isfile('odoo/odoo.py'):
                return 'odoo/odoo.py'
            elif os.path.isfile('odoo/odoo-bin'):
                return 'odoo/odoo-bin'
        else:
            if os.path.isfile('openerp-server'):
                return './openerp-server'
            elif os.path.isfile('odoo.py'):
                return './odoo.py'
            elif os.path.isfile('odoo-bin'):
                return './odoo-bin'
        return 'openerp7/openerp-server'

    def system_init(self):
        print 'init: started'
        debs = ['python', 'python-dateutil', 'python-decorator', 'python-docutils', 'python-feedparser',
                'python-imaging', 'python-jinja2', 'python-ldap', 'python-libxslt1', 'python-lxml', 'python-mako',
                'python-mock', 'python-openid', 'python-passlib', 'python-psutil', 'python-psycopg2', 'python-pybabel',
                'python-pychart', 'python-pydot', 'python-pyparsing', 'python-pypdf', 'python-reportlab',
                'python-requests', 'python-simplejson', 'python-tz', 'python-unittest2', 'python-vatnumber',
                'python-vobject', 'python-werkzeug', 'python-xlwt', 'python-yaml', 'python-gevent']
        debs += ["postgresql"]
        proc = subprocess.Popen(['sudo', 'apt-get', '--yes', '--force-yes', 'install'] + debs, stdout=open('/dev/null'))
        proc.communicate()
        print 'init: completed'
        return

    def _git_clone(self, url, branch, checkout_path):
        try:
            subprocess.check_output(['git', 'clone', '-b', branch, '--single-branch', url, checkout_path])
        except subprocess.CalledProcessError as e:
            raise e

    def _setup_odoo_configuration(self, config):
        # Setup openerp-server.conf file
        project_name = config['project']['name']

        config_filename = self.projects_home + '/' + project_name + '/openerp-server.conf'
        fos = open(config_filename, 'w')
        fos.write(
            '[options]\n; This is the password that allows database operations:\nadmin_passwd = %s\n' % project_name)
        if config['project'].get('has_addons', False):
            addons_path = self.projects_home + '/' + project_name + '/odoo/addons'
            addons_path = addons_path + ',' + self.projects_home + '/' + project_name + '/addons'
            fos.write('addons_path = %s\n' % (addons_path))
        fos.write('db_host = %s\ndb_port = %s\n' % (
        self.kutty_config['odoo_db']['host'], self.kutty_config['odoo_db']['port']))
        fos.write('db_user = %s\n' % project_name)
        fos.write('db_password = redhat19\n')
        fos.close()
        return

    def has_project_exits(self, project_name):
        if self.odoo_instances.count({'name': project_name}) == 0:
            return False
        return True

    def _find_unused_port(self):
        result_set = self.odoo_instances.find({}, {'port_no': 1, '_id': 0}).sort("port_no", 1)
        count = 8001
        port_no = str(count)
        for elm in result_set:
            if port_no != elm['port_no']:
                break
            else:
                count += 1
                port_no = str(count)

        return port_no

    def validate_config(self, config):
        if not config.get('project', False):
            return "project notation is not found"
        if not config['project'].get('sca', False):
            return "project/sca notation is not found"
        elif config['project']['sca'] not in ['download', 'link']:
            return "notation project/sca, don't have valid values download or link"
        return False

    def install(self, config):

        validate_result = self.validate_config(config)
        if validate_result:
            raise OAException(validate_result)

        project_name = config['project']['name']
        if self.has_project_exits(project_name):
            raise OAException('Project already exists')
        # os.chdir(self.projects_home)

        project_title = config['project']['title']
        port_no = self._find_unused_port()
        sca = config['project']['sca']
        self.odoo_instances.insert_one(
            {'title': project_title, 'name': project_name, 'status': 'Deploying', 'port_no': port_no, 'sca': sca})

        if 'download' == sca:
            git_url = config['git']['url']
            git_branch = config['git']['branch']

            print "Installing project", project_name
            # Download source code
            checkout_path = self.projects_home + '/' + project_name
            addons_checkout_path = None
            if config['project'].get('has_addons', False):
                checkout_path = checkout_path + '/odoo'
                addons_checkout_path = self.projects_home + '/' + project_name + '/addons'
            os.makedirs(checkout_path)

            try:
                self._git_clone(git_url, git_branch, checkout_path)
                if addons_checkout_path:
                    self._git_clone(config['addons']['url'], config['addons']['branch'], addons_checkout_path)
            except Exception as e:
                self.odoo_instances.delete_one({'name': project_name})
                shutil.rmtree(project_name)
                raise OAException("%s\nError while clone the code from repository" % e.message)
            self._create_odoo_db_user(project_name)
            self._setup_odoo_configuration(config)
        self._update_apache_config(project_name, port_no)

        self._update_server_status(project_name, 'Stopped')
        print "Installation Done"
        return

    def list_instance(self):
        ouput = []
        for elm in self.odoo_instances.find({}, {'_id': 0}):
            if elm["status"] == "Running":
                self._refresh_server_status(elm['name'])
            ouput.append(elm)

        return ouput

    def get_instance_info(self, name):
        return self.odoo_instances.find_one({'name': name}, {'_id': 0})

    def remove(self, project_name):
        if not self.has_project_exits(project_name):
            raise OAException("Project %s not exits" % project_name)
        os.chdir(self.projects_home)
        self.stop(project_name)
        sca = self.odoo_instances.find_one({'name': project_name}, {'_id': 0})['sca']
        if sca == 'download':
            shutil.rmtree(project_name)
        self._remove_apache_config(project_name)
        self.odoo_instances.delete_one({'name': project_name})
        print "Project %s removed successfully" % project_name
        return

    def _pid_kill(self, pid, port_no):
        if self._pid_exists(pid, port_no):
            ps = psutil.Process(pid)
            try:
                ps.terminate()
            except psutil.AccessDenied:
                return False
        return True

    def _pid_force_kill(self, pid, port_no):
        if self._pid_exists(pid, port_no):
            ps = psutil.Process(pid)
            try:
                ps.kill()
            except psutil.AccessDenied:
                return False
        return True

    def _pid_exists(self, pid, port_no):
        if psutil.pid_exists(pid):
            try:
                ps = psutil.Process(pid)
                cons = ps.connections()
                if cons and cons[0].laddr and str(cons[0].laddr[1]) == port_no:
                    return True
            except psutil.AccessDenied:
                return False
        return False

    def _get_pid(self, project_name):
        pid = self.odoo_instances.find_one({'name': project_name}, {'pid': 1, '_id': 0}).get('pid', False)
        if not pid:
            pid = '123456'
        return int(pid)

    def _start_odoo(self, project_name, upgrade=None):
        port_no = self.odoo_instances.find_one({'name': project_name}, {'port_no': 1, '_id': 0})['port_no']
        update = ""
        pid_file = tempfile.NamedTemporaryFile(delete=True)
        pid_filename = pid_file.name
        logfile = "%s/log/%s.log" % (self.dot_kutty_path, project_name)
        if upgrade is not None:
            update = "--update=%s" % upgrade
        os.system('%s --xmlrpc-port=%s --logfile=%s -c openerp-server.conf %s >/dev/null & echo $! > %s' % (
            self._startup_file_location(), port_no, logfile,  update, pid_filename))

        pid = pid_file.readline().rstrip()
        pid_file.close()
        self.odoo_instances.update_one({'name': project_name}, {'$set': {'pid': pid}})

    def stop(self, project_name):
        if not self.has_project_exits(project_name):
            raise OAException("Project %s not exits" % project_name)
        port_no = self.odoo_instances.find_one({'name': project_name}, {'port_no': 1, '_id': 0})['port_no']
        os.chdir(self.projects_home)
        print 'Stopping project ', project_name

        if self.server_status(project_name) in ['Stopped', 'Deploying', 'Stopping']:
            _return_msg = 'Server is not running or Deploying in progress'
            return False, _return_msg

        self._update_server_status(project_name, 'Stopping')
        os.chdir(project_name)
        pid = self._get_pid(project_name)
        if not self._pid_kill(pid, port_no):
            print 'Not able to kill the process. Still continue.'

        if self._pid_exists(pid, port_no):
            clean = False
            for count in range(1, 90):
                time.sleep(2)
                print "Waiting for shutdown[%s]" % (count)
                if not self._pid_exists(pid, port_no):
                    clean = True
                    break

            if not clean:
                print "No clean shutdown"
                self._pid_force_kill(pid, port_no)

        os.chdir(self.projects_home)
        self._update_server_status(project_name, 'Stopped')
        print 'Project stopped'
        return

    def kill(self, project_name):
        if not self.has_project_exits(project_name):
            raise OAException("Project %s not exits" % project_name)
        os.chdir(self.projects_home)
        print 'Stopping project ', project_name

        server_status = self.server_status(project_name)

        if server_status in ['Stopped', 'Deploying']:
            _return_msg = 'Server is not running or Deploying in progress'
            return False, _return_msg

        if server_status in ['Starting', 'Started']:
            _return_msg = 'Server is running'
            return False, _return_msg

        os.chdir(project_name)
        pid = self._get_pid(project_name)
        ps = psutil.Process(pid)
        ps.kill()
        os.chdir(self.projects_home)
        self._update_server_status(project_name, 'Stopped')
        print 'Project stopped'
        return

    def stop_all(self):
        result_set = self.odoo_instances.find({}, {'_id': 0}).sort("port_no", 1)
        for elm in result_set:
            self.stop(elm['name'])

    def start(self, project_name, upgrade=None):
        if not self.has_project_exits(project_name):
            raise OAException("Project %s not exits" % project_name)

        print 'Starting project ', project_name
        os.chdir(self.projects_home)
        os.chdir(project_name)

        if self.server_status(project_name) in ['Running', 'Deploying', 'Starting']:
            raise OAException('Already server running/Deploying in progress')

        self._update_server_status(project_name, "Starting")

        if upgrade is None:
            self._start_odoo(project_name)
        else:
            self._start_odoo(project_name, upgrade)

        os.chdir(self.projects_home)
        self._update_server_status(project_name, "Running")
        print 'Project started'
        return

    def start_all(self, upgrade=None):
        result_set = self.odoo_instances.find({}, {'_id': 0}).sort("port_no", 1)
        for elm in result_set:
            self.start(elm['name'], upgrade)

    def server_status(self, project_name):
        self._refresh_server_status(project_name)
        result_set = self.odoo_instances.find_one({'name': project_name}, {'status': 1, '_id': 0})
        if result_set is None:
            raise OAException('Project %s is not found' % project_name)
        return result_set['status']

    def _refresh_server_status(self, project_name):

        port_no = self.odoo_instances.find_one({'name': project_name}, {'port_no': 1, '_id': 0})['port_no']
        if self._pid_exists(self._get_pid(project_name), port_no):
            self._update_server_status(project_name, "Running")
        else:
            self._update_server_status(project_name, "Stopped")

    def _update_server_status(self, project_name, status):
        self.odoo_instances.update_one({'name': project_name}, {"$set": {'status': status}})

    def restart(self, project_name):
        self.stop(project_name)
        self.start(project_name)

    def upgradesrc(self, project_name):
        if not self.has_project_exits(project_name):
            raise OAException("Project %s not exits" % project_name)
        os.chdir(self.projects_home)
        print 'Upgrading project source only'
        self.stop(project_name)
        project_path = self.projects_home + '/' + project_name
        os.chdir(project_path)
        if os.path.isdir('addons'):
            os.chdir('addons')
        subprocess.call(['git', 'reset', '--hard'])
        subprocess.call(['git', 'pull'])
        self.start(project_name)
        print 'Project upgraded with source and started'
        return

    def upgrade(self, project_name, module="all"):
        if not self.has_project_exits(project_name):
            raise OAException("Project %s not exits" % project_name)
        os.chdir(self.projects_home)
        print 'Upgrading project ', project_name
        self.stop(project_name)
        project_path = self.projects_home + '/' + project_name
        os.chdir(project_path)
        if os.path.isdir('addons'):
            os.chdir('addons')
        subprocess.call(['git', 'reset', '--hard'])
        subprocess.call(['git', 'pull'])
        self.start(project_name, upgrade=module)
        print 'Project upgraded and started'
        return

    def updatedb(self, project_name, module="all"):
        if not self.has_project_exits(project_name):
            raise OAException("Project %s not exits" % project_name)
        print 'Updating DB of ', project_name
        self.stop(project_name)
        self.start(project_name, upgrade=module)
        print 'Project DB updated'
        return

    def switch(self, project_name, branch, module="all"):
        if not self.has_project_exits(project_name):
            raise OAException("Project %s not exits" % project_name)
        os.chdir(self.projects_home)
        print 'Switching into branch %s for project %s' % (branch, project_name)
        self.stop(project_name)
        project_path = self.projects_home + '/' + project_name
        os.chdir(project_path)
        if os.path.isdir('addons'):
            os.chdir('addons')
        subprocess.call(['git', 'reset', '--hard'])
        subprocess.call(['git', 'fetch'])
        subprocess.call(['git', 'checkout', branch, '&&', 'git', 'pull'])
        self.start(project_name, upgrade=module)
        print 'Branch swithced and started'
        return

    def send_log(self, project_name, to, from_email=None):
        if not self.has_project_exits(project_name):
            raise OAException("Project %s not exits" % project_name)
        os.chdir(self.projects_home)
        print '[Kutty] Sending log to %s of poject %s' % (to, project_name)
        logfile = '%s/log/openerp-server.log' % project_name
        fp = open(logfile, 'rb')
        # Create a text/plain message
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload((fp).read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename="openerp-server.log.txt")
        fp.close()

        msg = MIMEMultipart()
        msg.attach(attachment)

        email_config = self.kutty_config['email']
        smtp = email_config['smtp']

        from_id = "%s <%s>" % (email_config['name'], email_config['username'])
        msg['Subject'] = 'Server Log of %s' % project_name
        msg['From'] = from_id
        msg['To'] = to

        s = smtplib.SMTP(smtp, port=587)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(email_config['username'], email_config['password'])
        s.sendmail(msg['From'], msg['To'], msg.as_string())
        s.quit()
        return

    def _create_odoo_db_user(self, project_name):
        # # Setup db username
        try:
            conn = psycopg2.connect(database="template1", user=self.kutty_config['odoo_db']['username'],
                                    password=self.kutty_config['odoo_db']['password'],
                                    host=self.kutty_config['odoo_db']['host'],
                                    port=self.kutty_config['odoo_db']['port'])
            cur = conn.cursor()
            cur.execute('CREATE USER "%s" WITH CREATEDB NOCREATEUSER PASSWORD \'%s\'' % (project_name, "redhat19"))
            conn.commit()
            conn.close()
        except psycopg2.Error as e:
            print "Not able to create user"
            print e.pgerror


class OAException(Exception):
    pass
