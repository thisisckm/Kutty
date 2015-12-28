#!/usr/bin/python
import ConfigParser
import os
import os.path
import shutil
import signal
import subprocess
import sys
import time
# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__ = "advik"
__date__ = "$13 Sep, 2014 9:05:42 PM$"
__projects_home = None
__pid_file = '.pid'


if __projects_home is None:
    __projects_home = os.path.dirname(os.path.realpath(__file__))


def startup_file_location():
    if os.path.isfile('openerp-server'):
        return './openerp-server'
    return 'openerp7/openerp-server'

def init():
    print 'init: started'
    debs = ['python', 'python-dateutil', 'python-decorator', 'python-docutils', 'python-feedparser', 'python-imaging', 'python-jinja2', 'python-ldap', 'python-libxslt1', 'python-lxml', 'python-mako', 'python-mock', 'python-openid', 'python-passlib', 'python-psutil', 'python-psycopg2', 'python-pybabel', 'python-pychart', 'python-pydot', 'python-pyparsing', 'python-pypdf', 'python-reportlab', 'python-requests', 'python-simplejson', 'python-tz', 'python-unittest2', 'python-vatnumber', 'python-vobject', 'python-werkzeug', 'python-xlwt', 'python-yaml', 'python-gevent']
    debs += ["postgresql"]
    proc = subprocess.Popen(['sudo', 'apt-get', '--yes', '--force-yes', 'install'] + debs, stdout=open('/dev/null'))
    proc.communicate()
    print 'init: completed'
    return


def install(cfg_filename):
    
    cfg = ConfigParser.ConfigParser()    
    cfg.read(cfg_filename)
    project_name = cfg.get('project', 'name')
    project_port_no = cfg.get('project', 'port_no')
    git_url = cfg.get('git', 'url')
    git_branch = cfg.get('git', 'branch')
    
    print "Installing project", project_name
    os.chdir(__projects_home)
    if os.path.isdir(project_name):
        print 'Project already exists'
        return
    #Download source code    
    os.mkdir(project_name)        
    subprocess.call(['git', 'clone', '-b', git_branch, git_url, project_name])
    
    #Setup db username
    cmd = ['sudo', 'su', '-', 'postgres', '-c', 'createuser -s --createdb %s' % project_name]
    ps = subprocess.Popen(cmd, stdin=subprocess.PIPE) 
    ps.communicate()
    
    #Setup openerp-server.conf file
    os.chdir(project_name)
    fos = open('openerp-server.conf', 'w')
    fos.write('[options]\n; This is the password that allows database operations:\n; admin_passwd = admin\n')
    fos.write('db_host = False\nb_port = False\n')
    fos.write('db_user = %s\n' % project_name)
    fos.write('db_password = False\n')
    fos.write('xmlrpc_port = %s\n' % project_port_no)
    fos.write('logfile = log/openerp-server.log\nproxy_mode = True\n')
    fos.close()
    
    print "Installation Done"
    return

def remove(project_name, project_path):
    stop(project_name, project_path)
    shutil.rmtree(project_path)
    cmd = ['sudo', 'su', '-', 'postgres', '-c', 'dropuser %s' % project_name]
    ps = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    print "Project %s removed successfully" % project_name    
    return


def pid_kill(pid_file):
    pid = get_pid(pid_file)
    if pid_exists(pid):
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


def stop(project_name, project_path):
    print 'Stopping project ', project_name
    os.chdir(project_path)    
    if not pid_exists(get_pid(__pid_file)):
        print 'Server not running'
        return
    pid_kill(__pid_file)
    print 'Project stopped'
    return


def start(project_name, project_path):
    print 'Starting project ', project_name
    os.chdir(project_path)
    if pid_exists(get_pid(__pid_file)):
        print 'Already server running'
        return
    os.system('%s -c openerp-server.conf & echo $! > .pid'%startup_file_location())
    print 'Project started'
    return


def upgradesrc (project_name, project_path):
    print 'Upgrading project source only'
    stop(project_name, project_path)
    os.chdir(project_path)
    subprocess.call(['git', 'reset'])
    subprocess.call(['git', 'pull'])
    os.system('%s -c openerp-server.conf & echo $! > .pid'%startup_file_location())
    print 'Project upgraded with source and started'
    return


def upgrade(project_name, project_path):
    print 'Upgrading project ', project_name
    stop(project_name, project_path)
    os.chdir(project_path)
    subprocess.call(['git', 'reset'])
    subprocess.call(['git', 'pull'])
    os.system('%s -c openerp-server.conf --update=all & echo $! > .pid'%startup_file_location())
    print 'Project upgraded and started'
    return


def updatedb(project_name, project_path):
    print 'Updating DB of ', project_name
    stop(project_name, project_path)
    os.chdir(project_path)    
    os.system('%s -c openerp-server.conf --update=all & echo $! > .pid'%startup_file_location())
    print 'Project DB updated'
    return


def main():
    
    if not os.path.exists(__projects_home):
        os.mkdir(__projects_home)
        
    if len(sys.argv) == 2:
        cmd = sys.argv[1]
        if cmd == 'init':
            init()
    elif len(sys.argv) == 3:
        cmd = sys.argv[1]
        cfg_filename = sys.argv[2]
        if cmd == 'install' and os.path.isfile(cfg_filename):
            install(cfg_filename)
        elif cmd == 'start':
            project_name = sys.argv[2]
            project_path = __projects_home + os.path.sep + project_name
            if not os.path.isdir(project_path):
                print "Project ", project_name, " not found!"
            else:
                start(project_name, project_path)
        elif cmd == 'stop':
            project_name = sys.argv[2]
            project_path = __projects_home + os.path.sep + project_name
            if not os.path.isdir(project_path):
                print "Project ", project_name, " not found!"
            else:
                stop(project_name, project_path)
        elif cmd == 'restart':
            project_name = sys.argv[2]
            project_path = __projects_home + os.path.sep + project_name
            if not os.path.isdir(project_path):
                print "Project ", project_name, " not found!"
            else:
                stop(project_name, project_path)
                time.sleep(5)
                start(project_name, project_path)    
        elif cmd == 'remove':
            project_name = sys.argv[2]
            project_path = __projects_home + os.path.sep + project_name
            if not os.path.isdir(project_path):
                print "Project ", project_name, " not found!"
            else:
                remove(project_name, project_path)
        elif cmd == 'upgrade':
            project_name = sys.argv[2]
            project_path = __projects_home + os.path.sep + project_name
            if not os.path.isdir(project_path):
                print "Project ", project_name, " not found!"
            else:
                upgrade(project_name, project_path)
        elif cmd == 'upgradesrc':
            project_name = sys.argv[2]
            project_path = __projects_home + os.path.sep + project_name
            if not os.path.isdir(project_path):
                print "Project ", project_name, " not found!"
            else:
                upgradesrc(project_name, project_path)
        elif cmd == 'updatedb':
            project_name = sys.argv[2]
            project_path = __projects_home + os.path.sep + project_name
            if not os.path.isdir(project_path):
                print "Project ", project_name, " not found!"
            else:
                updatedb(project_name, project_path)
        elif cmd == 'log':
            import tailer
            project_name = sys.argv[2]
            project_log_file = __projects_home + os.path.sep + project_name + os.path.sep + 'log' + os.path.sep + 'openerp-server.log'
            print project_log_file
            for line in tailer.follow(open(project_log_file)):
                print line
    else:
        print 'argument is required'
    return

if __name__ == "__main__":
    main()

