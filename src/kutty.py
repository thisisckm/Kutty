#!/usr/bin/python
import os
import os.path
import argparse
import ConfigParser
from activity import server

# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__ = "advik"
__date__ = "$13 Sep, 2014 9:05:42 PM$"
__version__ = '0.1beta'


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

    parser_create = subparsers.add_parser('restart')
    parser_create.set_defaults(which='restart')
    parser_create.add_argument('project', help='Project server to be restart')

    parser_create = subparsers.add_parser('log')
    parser_create.set_defaults(which='log')
    parser_create.add_argument('project', help='Project server to be restart')

    parser_create = subparsers.add_parser('remove')
    parser_create.set_defaults(which='remove')
    parser_create.add_argument('project', help='Project server to be removed')

    args = vars(parser.parse_args())

    kutty_config = ConfigParser.ConfigParser()
    kutty_config.read("kutty.config")
    kutty_config = kutty_config._sections

    odooInstanceActivity = server.OdooInstanceActivity(kutty_config)

    if args['which'] == 'init':
        odooInstanceActivity.system_init()

    elif args['which'] == 'install':
        cfg_filename = args['config-file']
        config = config_file_dict(cfg_filename)
        odooInstanceActivity.install(config)

    elif args['which'] == 'start':
        project_name = args['project']
        odooInstanceActivity.start(project_name)

    elif args['which'] == 'stop':
        project_name = args['project']
        odooInstanceActivity.stop(project_name)

    elif args['which'] == "restart":
        project_name = args['project']
        odooInstanceActivity.restart(project_name)

    elif args['which'] == "remove":
        project_name = args['project']
        odooInstanceActivity.remove(project_name)

    elif args['which'] == 'upgrade':
        project_name = args['project']
        module = args['update']
        odooInstanceActivity.upgrade(project_name, module)

    elif args['which'] == 'upgradesrc':
        project_name = args['project']
        odooInstanceActivity.upgradesrc(project_name)

    elif args['which'] == 'updatedb':
        project_name = args['project']
        module = args['update']
        odooInstanceActivity.updatedb(project_name, module)

    elif args['which'] == 'switch':
        project_name = args['project']
        module = args['update']
        branch = args['branch']
        odooInstanceActivity.switch(project_name, branch, module)

    elif args['which'] == 'log':
        import tailer
        project_name = args['project']
        project_log_file = project_name + os.path.sep + 'log' + os.path.sep + 'openerp-server.log'
        print project_log_file
        for line in tailer.follow(open(project_log_file)):
            print line

    elif args['which'] == 'remove':
        project_name = args['project']
        odooInstanceActivity.remove(project_name)


    else:
        print args['which']

    return


if __name__ == "__main__":
    main()
