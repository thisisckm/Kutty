import os
import os.path
import shutil
import signal
import subprocess
import psycopg2
import sys
import tempfile
import time


class OdooInstanceActivity:
    def __init__(self, kutty_config):
        self.kutty_config = kutty_config
        self.projects_home = kutty_config['default']['project_home']
        self.pid_file = '.pid'

        try:
            host = kutty_config['odoo_db']['host']
            port = kutty_config['odoo_db']['port']
            user = kutty_config['odoo_db']['username']
            password = kutty_config['odoo_db']['password']
            conn = psycopg2.connect("dbname='template1' host='%s' port='%s' user='%s' password='%s'" % (host,port,user,password))
            conn.close()
        except:
            print "Can't able to connect to the database"
            sys.exit(1)

        if not os.path.exists(self.projects_home):
            os.mkdir(self.projects_home)


    def _update_apache_config(self, server_name, portno):
        template = "<VirtualHost *:80>\n"
        template = template + "ServerName %s\n"
        template = template + "ProxyPass / http://localhost:%s/\n"
        template = template + "ProxyPassReverse / http://localhost:%s/\n"
        template = template + "</VirtualHost>"

        output = template % (server_name, portno, portno)
        temp_file = tempfile.gettempdir() + os.path.sep + server_name
        conf_file = "%s%s%s.conf" %(self.kutty_config['apache']['sa_path'], os.path.sep, server_name)
        link_file = "%s%s%s.conf" %(self.kutty_config['apache']['se_path'], os.path.sep, server_name)

        ostream = open(temp_file, 'w')
        ostream.write(output)
        ostream.flush()
        ostream.close()

        command = ['sudo', 'cp', temp_file,conf_file]
        subprocess.Popen(command, stdin=subprocess.PIPE)
        command = ['sudo', 'ln', '-s', conf_file, link_file]
        subprocess.Popen(command, stdin=subprocess.PIPE)
        command = ['sudo','apachectl', '-k', 'graceful']
        subprocess.Popen(command, stdin=subprocess.PIPE)

    def _remove_apache_config(self,server_name):
        conf_file = "%s%s%s.conf" %(self.kutty_config['apache']['sa_path'], os.path.sep, server_name)
        link_file = "%s%s%s.conf" %(self.kutty_config['apache']['se_path'], os.path.sep, server_name)
        command = ['sudo', 'rm', conf_file, link_file]
        subprocess.Popen(command, stdin=subprocess.PIPE)
        command = ['sudo','apachectl', '-k', 'graceful']
        subprocess.Popen(command, stdin=subprocess.PIPE)

    def _startup_file_location(self):
        if os.path.isdir('odoo'):
            return 'odoo/openerp-server'
        if os.path.isfile('openerp-server'):
            return './openerp-server'
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
        subprocess.call(['git', 'clone', '-b', branch, url, checkout_path])

    def _setup_odoo_configuration(self, config):
        # Setup openerp-server.conf file
        project_name = config['project']['name']
        project_port_no = config['project']['port_no']

        os.chdir(project_name)
        fos = open('openerp-server.conf', 'w')
        fos.write(
            '[options]\n; This is the password that allows database operations:\n; admin_passwd = %s\n' % project_name)
        if config['has_addons']:
            addons_path = self.projects_home + '/' + project_name + '/odoo/addons'
            addons_path = addons_path + ',' + self.projects_home + '/' + project_name + '/addons'
            fos.write('addons_path = %s\n' % (addons_path))
        fos.write('db_host = %s\ndb_port = %s\n' % (self.kutty_config['odoo_db']['host'],self.kutty_config['odoo_db']['port']))
        fos.write('db_user = %s\n' % project_name)
        fos.write('db_password = redhat19\n')
        fos.write('xmlrpc_port = %s\n' % project_port_no)
        fos.write('logfile = log/openerp-server.log\nproxy_mode = True\n')
        fos.close()

    def install(self, config):
        os.chdir(self.projects_home)
        project_name = config['project']['name']
        git_url = config['git']['url']
        git_branch = config['git']['branch']

        print "Installing project", project_name
        if os.path.isdir(project_name):
            print 'Project already exists'
            return
        # Download source code
        checkout_path = project_name
        addons_checkout_path = None
        if config['has_addons']:
            checkout_path = checkout_path + '/odoo'
            addons_checkout_path = project_name + '/addons'
        os.makedirs(checkout_path)

        self._git_clone(git_url, git_branch, checkout_path)
        if addons_checkout_path:
            self._git_clone(config['addons']['url'], config['addons']['branch'], addons_checkout_path)

        self._create_odoo_db_user(project_name)
        self._setup_odoo_configuration(config)
        self._update_apache_config(project_name, config['project']['port_no'])

        print "Installation Done"
        return

    def remove(self, project_name):
        os.chdir(self.projects_home)
        self.stop(project_name)
        shutil.rmtree(project_name)
        self._remove_apache_config(project_name)
        print "Project %s removed successfully" % project_name
        return

    def _pid_kill(self, pid_file):
        pid = self._get_pid(pid_file)
        if self._pid_exists(pid):
            os.kill(int(pid), signal.SIGINT)
        return

    def _pid_exists(self, pid):
        return os.path.exists('/proc/' + pid)

    def _get_pid(self, pid_file):
        pid = '0'
        if os.path.isfile(pid_file):
            fis = open(pid_file, 'r')
            pid = fis.readline().rstrip()
            fis.close()
        return pid

    def stop(self, project_name):
        os.chdir(self.projects_home)
        print 'Stopping project ', project_name
        os.chdir(project_name)
        if not self._pid_exists(self._get_pid(self.pid_file)):
            print 'Server not running'
            os.chdir('..')
            return
        self._pid_kill(self.pid_file)
        print 'Project stopped'
        os.chdir('..')
        return

    def start(self, project_name):
        os.chdir(self.projects_home)
        print 'Starting project ', project_name
        os.chdir(project_name)
        if self._pid_exists(self._get_pid(self.pid_file)):
            print 'Already server running'
            return
        os.system('%s -c openerp-server.conf & echo $! > .pid' % self._startup_file_location())
        print 'Project started'
        return

    def server_status(self, project_name):
        os.chdir(self.projects_home)
        os.chdir(project_name)
        if self._pid_exists(self._get_pid(self.pid_file)):
            return 'running'
        else:
            return 'stopped'

    def restart(self,project_name):
        self.stop(project_name)
        while True:
            time.sleep(2)
            if self.server_status(project_name) == 'stopped':
                break
        self.start(project_name)


    def upgradesrc(self, project_name):
        os.chdir(self.projects_home)
        print 'Upgrading project source only'
        self.stop(project_name)
        project_path = self.projects_home + '/' + project_name
        os.chdir(project_path)
        os.path.isdir('addons')
        os.chdir('addons')
        subprocess.call(['git', 'reset', '--hard'])
        subprocess.call(['git', 'pull'])
        os.chdir(project_path)
        os.system('%s -c openerp-server.conf & echo $! > .pid' % self._startup_file_location())
        print 'Project upgraded with source and started'
        return

    def upgrade(self, project_name, module):
        os.chdir(self.projects_home)
        print 'Upgrading project ', project_name
        self.stop(project_name)
        project_path = self.projects_home + '/' + project_name
        os.chdir(project_path)
        os.path.isdir('addons')
        os.chdir('addons')
        subprocess.call(['git', 'reset', '--hard'])
        subprocess.call(['git', 'pull'])
        os.chdir(project_path)
        os.system('%s -c openerp-server.conf --update=%s & echo $! > .pid' % (self._startup_file_location(), module))
        print 'Project upgraded and started'
        return

    def updatedb(self, project_name, module):
        os.chdir(self.projects_home)
        print 'Updating DB of ', project_name
        self.stop(project_name)
        os.chdir(project_name)
        os.system('%s -c openerp-server.conf --update=%s & echo $! > .pid' % (self._startup_file_location(), module))
        print 'Project DB updated'
        return

    def switch(self, project_name, branch, module):
        os.chdir(self.projects_home)
        print 'Switching into branch %s for project %s' % (branch, project_name)
        self.stop(project_name)
        project_path = self.projects_home + '/' + project_name
        os.chdir(project_path)
        os.path.isdir('addons')
        os.chdir('addons')
        subprocess.call(['git', 'reset', '--hard'])
        subprocess.call(['git', 'fetch'])
        subprocess.call(['git', 'checkout', branch, '&&', 'git', 'pull'])
        os.chdir(project_path)
        os.system('%s -c openerp-server.conf --update=%s & echo $! > .pid' % (self._startup_file_location(), module))
        print 'Branch swithced and started'
        return

    def _create_odoo_db_user(self,project_name):
        # # Setup db username
        try:
            conn = psycopg2.connect(database="template1", user=self.kutty_config['odoo_db']['username'], password=self.kutty_config['odoo_db']['password'], host=self.kutty_config['odoo_db']['host'], port=self.kutty_config['odoo_db']['port'])
            cur = conn.cursor()
            cur.execute('CREATE USER "%s" WITH CREATEDB NOCREATEUSER PASSWORD \'%s\'' % (project_name, "redhat19"))
            conn.commit()
            conn.close()
        except psycopg2.Error as e:
            print "Not able to create user"
            print e.pgerror

