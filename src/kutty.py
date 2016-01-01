#!/usr/bin/python
import ConfigParser
import os
import os.path
import shutil
import signal
import subprocess
import argparse
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
    fos = open('openerp-server.conf', 'w')
    fos.write('[options]\n; This is the password that allows database operations:\n; admin_passwd = %s\n' % project_name)
    fos.write('db_host = localhost\ndb_port = 5432\n')
    fos.write('db_user = %s\n' % project_name)
    fos.write('db_password = redhat19\n')
    fos.write('xmlrpc_port = %s\n' % project_port_no)
    fos.write('logfile = log/openerp-server.log\nproxy_mode = True\n')
    fos.close()
    
    print "Installation Done"
    return


def remove(project_name):
    stop(project_name)
    shutil.rmtree(project_name)
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


def stop(project_name):
    print 'Stopping project ', project_name
    os.chdir(project_name)
    if not pid_exists(get_pid(__pid_file)):
        print 'Server not running'
        os.chdir('..')
        return
    pid_kill(__pid_file)
    print 'Project stopped'
    os.chdir('..')
    return


def start(project_name):
    print 'Starting project ', project_name
    os.chdir(project_name)
    if pid_exists(get_pid(__pid_file)):
        print 'Already server running'
        return
    os.system('%s -c openerp-server.conf & echo $! > .pid'%startup_file_location())
    print 'Project started'
    return


def upgradesrc (project_name):
    print 'Upgrading project source only'
    stop(project_name)
    os.chdir(project_name)
    subprocess.call(['git', 'reset', '--hard'])
    subprocess.call(['git', 'pull'])
    os.system('%s -c openerp-server.conf & echo $! > .pid'%startup_file_location())
    print 'Project upgraded with source and started'
    return


def upgrade(project_name):
    print 'Upgrading project ', project_name
    stop(project_name)
    os.chdir(project_name)
    subprocess.call(['git', 'reset', '--hard'])
    subprocess.call(['git', 'pull'])
    os.system('%s -c openerp-server.conf --update=all & echo $! > .pid'%startup_file_location())
    print 'Project upgraded and started'
    return


def updatedb(project_name):
    print 'Updating DB of ', project_name
    stop(project_name)
    os.chdir(project_name)
    os.system('%s -c openerp-server.conf --update=all & echo $! > .pid'%startup_file_location())
    print 'Project DB updated'
    return


def extant_file(filepath):
    """
    'Type' for argparse - checks that file exists but does not open.
    """
    if not os.path.exists(filepath):
        # Argparse uses the ArgumentTypeError to give a rejection message like:
        # error: argument input: x does not exist
        raise argparse.ArgumentTypeError("{0} does not exist".format(filepath))
    return filepath


def main():
    
    if not os.path.exists(__projects_home):
        os.mkdir(__projects_home)
    os.chdir(__projects_home)

    parser = argparse.ArgumentParser(description='Kutty - from Axcensa')
    subparsers = parser.add_subparsers(title='subcommands', description='valid subcommands', help='additional help')

    parser_create = subparsers.add_parser('init')
    parser_create.set_defaults(which='init')

    parser_create = subparsers.add_parser('install')
    parser_create.set_defaults(which='install')
    parser_create.add_argument('config-file', help='Project configuration file', type=extant_file)

    parser_create = subparsers.add_parser('upgrade')
    parser_create.set_defaults(which='upgrade')
    parser_create.add_argument('project', help='Project name to be upgraded')

    parser_create = subparsers.add_parser('update')
    parser_create.set_defaults(which='upgrade')
    parser_create.add_argument('project', help='Project name to be update')

    parser_create = subparsers.add_parser('upgradesrc')
    parser_create.set_defaults(which='upgrade')
    parser_create.add_argument('project', help='Project name to be upgraded only the source')

    parser_create = subparsers.add_parser('stop')
    parser_create.set_defaults(which='stop')
    parser_create.add_argument('project', help='Project server to be Stopped', type=extant_file)

    parser_create = subparsers.add_parser('start')
    parser_create.set_defaults(which='start')
    parser_create.add_argument('project', help='Project server to be Start', type=extant_file)

    parser_create = subparsers.add_parser('restart')
    parser_create.set_defaults(which='restart')
    parser_create.add_argument('project', help='Project server to be restart', type=extant_file)

    parser_create = subparsers.add_parser('log')
    parser_create.set_defaults(which='log')
    parser_create.add_argument('project', help='Project server to be restart', type=extant_file)

    args = vars(parser.parse_args())

    if args['which'] == 'init':
        init()

    elif args['which'] == 'install':
        cfg_filename = args['config-file']
        install(cfg_filename)

    elif args['which'] == 'start':
        project_name = args['project']
        start(project_name)

    elif args['which'] == 'stop':
        project_name = args['project']
        stop(project_name)

    elif args['which'] == 'restart':
        project_name = args['project']
        stop(project_name)
        time.sleep(5)
        start(project_name)

    elif args['which'] == 'remove':
        project_name = args['project']
        remove(project_name)

    elif args['which'] == 'upgrade':
        project_name = args['project']
        upgrade(project_name)

    elif args['which'] == 'upgradesrc':
        project_name = args['project']
        upgradesrc(project_name)

    elif args['which'] == 'updatedb':
        project_name = args['project']
        updatedb(project_name)

    elif args['which'] == 'log':
        import tailer
        project_name = args['project']
        project_log_file = project_name + os.path.sep + 'log' + os.path.sep + 'openerp-server.log'
        print project_log_file
        for line in tailer.follow(open(project_log_file)):
            print line

    else:
        print args['which']

    return

if __name__ == "__main__":
    main()

