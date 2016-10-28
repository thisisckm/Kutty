#!/usr/bin/python
import ConfigParser
import argparse
import getpass
import os
import os.path

from kutty.kuttyws import KuttyWS
from kutty.odoo import activity as odoo_activity
from kutty.usrmng import activity as usermng_activity
from util import configuration

# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__ = "advik"
__date__ = "$13 Sep, 2014 9:05:42 PM$"
__version__ = '0.9beta'


def get_user_credential():
    username = raw_input('Username: ')
    pwd = getpass.getpass('Password: ')
    return username, pwd

def extant_file(filepath):
    if not os.path.exists(filepath):
        raise argparse.ArgumentTypeError("{0} does not exist".format(filepath))
    return filepath


def config_file_dict(cfg_filename):
    cfg = ConfigParser.ConfigParser()
    cfg.read(cfg_filename)
    return_value = dict(cfg._sections)
    if return_value.has_key('addons'):
        return_value['has_addons'] = True
    else:
        return_value['has_addons'] = False
    return return_value

def main():
    parser = argparse.ArgumentParser(description='Kutty - from Axcensa\nVersion %s'%__version__)
    subparsers = parser.add_subparsers(title='subcommands', description='valid subcommands', help='additional help')

    parser_create = subparsers.add_parser('init')
    parser_create.set_defaults(which='init')

    parser_create = subparsers.add_parser('install')
    parser_create.set_defaults(which='install')
    parser_create.add_argument('config-file', help='Project configuration file', type=extant_file)

    parser_create = subparsers.add_parser('list')
    parser_create.set_defaults(which='list')

    parser_create = subparsers.add_parser('upgrade')
    parser_create.set_defaults(which='upgrade')
    parser_create.add_argument('project', help='Project name to be upgraded')
    parser_create.add_argument('--update', default="all", help='Module to be updated')

    parser_create = subparsers.add_parser('updatedb')
    parser_create.set_defaults(which='updatedb')
    parser_create.add_argument('project', help='Project name to be update')
    parser_create.add_argument('--update', default="all", help='Module to be updated')

    parser_create = subparsers.add_parser('upgradesrc')
    parser_create.set_defaults(which='upgradesrc')
    parser_create.add_argument('project', help='Project name to be upgraded only the source')

    parser_create = subparsers.add_parser('switch')
    parser_create.set_defaults(which='switch')
    parser_create.add_argument('project', help='Project name to be where switch of branch')
    parser_create.add_argument('branch', help='Branch to be switched')
    parser_create.add_argument('--update', default="all", help='Module to be updated')

    parser_create = subparsers.add_parser('stop')
    parser_create.set_defaults(which='stop')
    parser_create.add_argument('project', help='Project server to be Stopped')

    parser_create = subparsers.add_parser('start')
    parser_create.set_defaults(which='start')
    parser_create.add_argument('project', help='Project server to be Start')

    parser_create = subparsers.add_parser('startall')
    parser_create.set_defaults(which='startall')

    parser_create = subparsers.add_parser('restart')
    parser_create.set_defaults(which='restart')
    parser_create.add_argument('project', help='Project server to be restart')

    parser_create = subparsers.add_parser('log')
    parser_create.set_defaults(which='log')
    parser_create.add_argument('project', help='Project server to be restart')

    parser_create = subparsers.add_parser('remove')
    parser_create.set_defaults(which='remove')
    parser_create.add_argument('project', help='Project server to be removed')

    parser_create = subparsers.add_parser('sendlog')
    parser_create.set_defaults(which='sendlog')
    parser_create.add_argument('project', help='Log file of the project')

    # User Management - Arguemnet Process
    parser_create = subparsers.add_parser('adduser')
    parser_create.set_defaults(which='adduser')
    parser_create.add_argument('username', help='New user to be added ')

    parser_create = subparsers.add_parser('listuser')
    parser_create.set_defaults(which='listuser')

    parser_create = subparsers.add_parser('deluser')
    parser_create.set_defaults(which='deluser')
    parser_create.add_argument('username', help='user to be removed ')

    parser_create = subparsers.add_parser('enableusr')
    parser_create.set_defaults(which='enableusr')
    parser_create.add_argument('username', help='user to be enabled')

    parser_create = subparsers.add_parser('disableusr')
    parser_create.set_defaults(which='disableusr')
    parser_create.add_argument('username', help='user to be disabled')

    parser_create = subparsers.add_parser('chgpwd')
    parser_create.set_defaults(which='chgpwd')
    parser_create.add_argument('username', help='user\'s password to be changed')

    # Web Service - Parameter
    parser_create = subparsers.add_parser('startws')
    parser_create.set_defaults(which='startws')

    parser_create = subparsers.add_parser('stopws')
    parser_create.set_defaults(which='stopws')

    args = vars(parser.parse_args())

    # Web Service Handling

    if args['which'] in ['startws', 'stopws']:

        kuttyWS = KuttyWS()

        if args['which'] == 'startws':
            kuttyWS.start_ws_server()
        elif args['which'] == 'stopws':
            kuttyWS.stop_ws_server()

    else:

        kutty_config = ConfigParser.ConfigParser()
        cnf_filename = configuration.find_config_file()
        kutty_config.read(cnf_filename)
        kutty_config = kutty_config._sections
        odooInstanceActivity = odoo_activity.OdooInstanceActivity(kutty_config)
        userManagementActivity = usermng_activity.UserManagementActivity()

        if args['which'] == 'init':
            odooInstanceActivity.system_init()

        elif args['which'] == 'install':
            usr, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(usr, pwd)):
                    cfg_filename = args['config-file']
                    config = config_file_dict(cfg_filename)
                    odooInstanceActivity.install(config)
            except usermng_activity.UMException as ex:
                print ex.message
            except odoo_activity.OAException as ex:
                print ex.message

        elif args['which'] == 'list':
            usr, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(usr, pwd)):
                    for elm in odooInstanceActivity.list_instance():
                        print elm
            except usermng_activity.UMException as ex:
                print ex.message

        elif args['which'] == 'start':
            usr, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(usr, pwd)):
                    project_name = args['project']
                    odooInstanceActivity.start(project_name)
            except usermng_activity.UMException as ex:
                print ex.message
            except odoo_activity.OAException as ex:
                print ex.message

        elif args['which'] == 'startall':
            usr, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(usr, pwd)):
                    odooInstanceActivity.start_all()
            except usermng_activity.UMException as ex:
                print ex.message
            except odoo_activity.OAException as ex:
                print ex.message

        elif args['which'] == 'stop':
            usr, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(usr, pwd)):
                    project_name = args['project']
                    odooInstanceActivity.stop(project_name)
            except usermng_activity.UMException as ex:
                print ex.message
            except odoo_activity.OAException as ex:
                print ex.message

        elif args['which'] == "restart":
            usr, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(usr, pwd)):
                    project_name = args['project']
                    odooInstanceActivity.restart(project_name)
            except usermng_activity.UMException as ex:
                print ex.message
            except odoo_activity.OAException as ex:
                print ex.message

        elif args['which'] == "remove":
            usr, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(usr, pwd)):
                    project_name = args['project']
                    odooInstanceActivity.remove(project_name)
            except usermng_activity.UMException as ex:
                print ex.message
            except odoo_activity.OAException as ex:
                print ex.message

        elif args['which'] == 'upgrade':
            usr, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(usr, pwd)):
                    project_name = args['project']
                    module = args['update']
                    odooInstanceActivity.upgrade(project_name, module)
            except usermng_activity.UMException as ex:
                print ex.message
            except odoo_activity.OAException as ex:
                print ex.message

        elif args['which'] == 'upgradesrc':
            usr, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(usr, pwd)):
                    project_name = args['project']
                    odooInstanceActivity.upgradesrc(project_name)
            except usermng_activity.UMException as ex:
                print ex.message
            except odoo_activity.OAException as ex:
                print ex.message

        elif args['which'] == 'updatedb':
            usr, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(usr, pwd)):
                    project_name = args['project']
                    module = args['update']
                    odooInstanceActivity.updatedb(project_name, module)
            except usermng_activity.UMException as ex:
                print ex.message
            except odoo_activity.OAException as ex:
                print ex.message

        elif args['which'] == 'switch':
            usr, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(usr, pwd)):
                    project_name = args['project']
                    module = args['update']
                    branch = args['branch']
                    odooInstanceActivity.switch(project_name, branch, module)
            except usermng_activity.UMException as ex:
                print ex.message
            except odoo_activity.OAException as ex:
                print ex.message

        elif args['which'] == 'sendlog':
            usr, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(usr, pwd)):
                    project_name = args['project']
                    user_profile = userManagementActivity.get_user(usr)
                    odooInstanceActivity.send_log(project_name, user_profile['email'])
            except usermng_activity.UMException as ex:
                print ex.message
            except odoo_activity.OAException as ex:
                print ex.message

        elif args['which'] == 'log':
            import tailer
            project_name = args['project']
            project_log_file = project_name + os.path.sep + 'log' + os.path.sep + 'openerp-server.log'
            print project_log_file
            for line in tailer.follow(open(project_log_file)):
                print line

        elif args['which'] == 'remove':
            usr, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(usr, pwd)):
                    project_name = args['project']
                    odooInstanceActivity.remove(project_name)
            except usermng_activity.UMException as ex:
                print ex.message
            except odoo_activity.OAException as ex:
                print ex.message

        elif args['which'] == 'adduser':
            user, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(user, pwd)):
                    new_username = args['username']
                    new_pwd = getpass.getpass('Password For New User %s: ' % new_username)

                    msg = 'Super User?'
                    type = 'normal'
                    is_super = raw_input("%s (y/N) " % msg).lower() == 'y'
                    if is_super:
                        type = 'admin'
                    userManagementActivity.adduser(new_username, new_pwd, type=type)
            except usermng_activity.UMException as exp:
                print exp.message

        elif args['which'] == 'listuser':
            user, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(user, pwd)):
                    print 'Username\t\tType\t\tStatus'
                    print '----------------------------------------------'
                    for elm in userManagementActivity.listuser():
                        print '%s\t\t\t%s\t\t%s' % (elm['user'].strip(), elm['type'], elm['active'])
            except usermng_activity.UMException as ex:
                print ex.message

        elif args['which'] == 'deluser':
            user, pwd = get_user_credential()
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(user, pwd)):
                    username = args['username']
                    msg = 'Are sure to remove this user %s ?' % username
                    approved = raw_input("%s (y/N) " % msg).lower() == 'y'
                    if approved:
                        userManagementActivity.deluser(username)
            except usermng_activity.UMException as ex:
                print ex.message

        elif args['which'] == 'enableusr':
            user, pwd = get_user_credential()
            username = args['username']
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(user, pwd)):
                    userManagementActivity.activitate_user(username, True)
            except usermng_activity.UMException as ex:
                print ex.message

        elif args['which'] == 'disableusr':
            user, pwd = get_user_credential()
            username = args['username']
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(user, pwd)):
                    userManagementActivity.activitate_user(username, False)
            except usermng_activity.UMException as ex:
                print ex.message

        elif args['which'] == 'chgpwd':
            user, pwd = get_user_credential()
            username = args['username']
            try:
                if userManagementActivity.check_authentication(usermng_activity.UserCredential(user, pwd)):
                    while True:
                        new_pwd = getpass.getpass('New Password For User %s: ' % username)
                        retype_new_pwd = getpass.getpass('Re-Type New Password: ')
                        if new_pwd == retype_new_pwd:
                            userManagementActivity.change_password(username, new_pwd)
                            break
                        else:
                            print 'Password mismatch, please try again'
            except usermng_activity.UMException as ex:
                print ex.message

    return


if __name__ == "__main__":
    main()
