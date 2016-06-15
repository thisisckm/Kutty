import ConfigParser
import os
import os.path
import shutil
import signal
import subprocess

class ServerActivity:


    def __init__(self, projects_home, server_list_file):
        self.projects_home = projects_home
        self.server_list_file = server_list_file

    def startup_file_location(self):
        if os.path.isdir('odoo'):
            return 'odoo/openerp-server'
        if os.path.isfile('openerp-server'):
            return './openerp-server'
        return 'openerp7/openerp-server'

    def system_init(self):
        print 'init: started'
        debs = ['python', 'python-dateutil', 'python-decorator', 'python-docutils', 'python-feedparser', 'python-imaging', 'python-jinja2', 'python-ldap', 'python-libxslt1', 'python-lxml', 'python-mako', 'python-mock', 'python-openid', 'python-passlib', 'python-psutil', 'python-psycopg2', 'python-pybabel', 'python-pychart', 'python-pydot', 'python-pyparsing', 'python-pypdf', 'python-reportlab', 'python-requests', 'python-simplejson', 'python-tz', 'python-unittest2', 'python-vatnumber', 'python-vobject', 'python-werkzeug', 'python-xlwt', 'python-yaml', 'python-gevent']
        debs += ["postgresql"]
        proc = subprocess.Popen(['sudo', 'apt-get', '--yes', '--force-yes', 'install'] + debs, stdout=open('/dev/null'))
        proc.communicate()
        print 'init: completed'
        return


    def install(self,cfg_filename):

        cfg = ConfigParser.ConfigParser()
        cfg.read(cfg_filename)
        project_name = cfg.get('project', 'name')
        project_port_no = cfg.get('project', 'port_no')
        git_url = cfg.get('git', 'url')
        git_branch = cfg.get('git', 'branch')
        is_addons_deploy = False
        addons_git_url = None
        addons_git_branch = None
        if cfg.has_section('addons'):
            is_addons_deploy = True
            addons_git_url = cfg.get('addons', 'url')
            addons_git_branch = cfg.get('addons', 'branch')

        print "Installing project", project_name
        if os.path.isdir(project_name):
            print 'Project already exists'
            return
        #Download source code
        checkout_path = project_name
        addons_checkout_path = None
        if is_addons_deploy:
            checkout_path = checkout_path + '/odoo'
            addons_checkout_path = project_name + '/addons'
        os.makedirs(checkout_path)

        subprocess.call(['git', 'clone', '-b', git_branch, git_url, checkout_path])
        if addons_checkout_path:
            subprocess.call(['git', 'clone', '-b', addons_git_branch, addons_git_url, addons_checkout_path])

        #Setup db username
        cmd = ['sudo', 'su', '-', 'postgres', '-c', 'createuser -s --createdb %s' % project_name]
        ps = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        ps.communicate()

        #Setup openerp-server.conf file
        os.chdir(project_name)
        fos = open('openerp-server.conf', 'w')
        fos.write('[options]\n; This is the password that allows database operations:\n; admin_passwd = %s\n' % project_name)
        if is_addons_deploy:
            addons_path = self.projects_home + '/' + project_name + '/odoo/addons'
            addons_path = addons_path + ',' + self.projects_home + '/' + project_name + '/addons'
            fos.write('addons_path = %s\n' % (addons_path))
        fos.write('db_host = localhost\ndb_port = 5432\n')
        fos.write('db_user = %s\n' % project_name)
        fos.write('db_password = redhat19\n')
        fos.write('xmlrpc_port = %s\n' % project_port_no)
        fos.write('logfile = log/openerp-server.log\nproxy_mode = True\n')
        fos.close()

        os.chdir(self.projects_home)
        with open(self.server_list_file, mode='a') as server_list_file:
            server_list_file.write('"%s" "%s"\n'%(project_name, project_name))

        print "Installation Done"
        return


    def remove(self,project_name):
        self.stop(project_name)
        shutil.rmtree(project_name)
        cmd = ['sudo', 'su', '-', 'postgres', '-c', 'dropuser %s' % project_name]
        ps = subprocess.Popen(cmd, stdin=subprocess.PIPE)

        print "Project %s removed successfully" % project_name
        return


    def pid_kill(self,pid_file):
        pid = self.get_pid(pid_file)
        if self.pid_exists(pid):
            os.kill(int(pid), signal.SIGINT)
        return


    def pid_exists(pid):
        return os.path.exists('/proc/' + pid)


    def get_pid(pid_file):
        pid = '0'
        if os.path.isfile(pid_file):
            fis = open(pid_file, 'r')
            pid = fis.readline().rstrip()
            fis.close()
        return pid


    def stop(self,project_name):
        print 'Stopping project ', project_name
        os.chdir(project_name)
        if not self.pid_exists(self.get_pid(self.pid_file)):
            print 'Server not running'
            os.chdir('..')
            return
        self.pid_kill(self.pid_file)
        print 'Project stopped'
        os.chdir('..')
        return


    def start(self,project_name):
        print 'Starting project ', project_name
        os.chdir(project_name)
        if self.pid_exists(self.get_pid(self.pid_file)):
            print 'Already server running'
            return
        os.system('%s -c openerp-server.conf & echo $! > .pid'%self.startup_file_location())
        print 'Project started'
        return


    def upgradesrc (self,project_name):
        print 'Upgrading project source only'
        self.stop(project_name)
        project_path = self.projects_home + '/' + project_name
        os.chdir(project_path)
        os.path.isdir('addons')
        os.chdir('addons')
        subprocess.call(['git', 'reset', '--hard'])
        subprocess.call(['git', 'pull'])
        os.chdir(project_path)
        os.system('%s -c openerp-server.conf & echo $! > .pid'%self.startup_file_location())
        print 'Project upgraded with source and started'
        return


    def upgrade(self,project_name, module):
        print 'Upgrading project ', project_name
        self.stop(project_name)
        project_path = self.projects_home + '/' + project_name
        os.chdir(project_path)
        os.path.isdir('addons')
        os.chdir('addons')
        subprocess.call(['git', 'reset', '--hard'])
        subprocess.call(['git', 'pull'])
        os.chdir(project_path)
        os.system('%s -c openerp-server.conf --update=%s & echo $! > .pid'%(self.startup_file_location(), module))
        print 'Project upgraded and started'
        return


    def updatedb(self,project_name, module):
        print 'Updating DB of ', project_name
        self.stop(project_name)
        os.chdir(project_name)
        os.system('%s -c openerp-server.conf --update=%s & echo $! > .pid'%(self.startup_file_location(), module))
        print 'Project DB updated'
        return


    def switch(self,project_name, branch, module):
        print 'Switching into branch %s for project %s'%(branch, project_name)
        self.stop(project_name)
        project_path = self.projects_home + '/' + project_name
        os.chdir(project_path)
        os.path.isdir('addons')
        os.chdir('addons')
        subprocess.call(['git', 'reset', '--hard'])
        subprocess.call(['git', 'fetch'])
        subprocess.call(['git', 'checkout', branch, '&&', 'git', 'pull'])
        os.chdir(project_path)
        os.system('%s -c openerp-server.conf --update=%s & echo $! > .pid'%(self.startup_file_location(), module))
        print 'Branch swithced and started'
        return
