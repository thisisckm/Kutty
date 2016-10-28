#!/usr/bin/python

import ConfigParser
import os
import getpass
import shutil

from util import configuration

config_home_path = configuration.get_home_path()

if not os.path.isdir(config_home_path):
    os.mkdir(config_home_path)

config = ConfigParser.RawConfigParser()

# Project Home
project_home = raw_input('Project Home: ').strip()
if project_home:
    if not os.path.isdir(project_home):
        os.mkdir(project_home)
    config.add_section('general')
    config.set('general', "project_home", project_home)

# apache configuration
apache_sa_path = '/etc/apache2/sites-available'
apache_se_path = '/etc/apache2/sites-enabled'
config.add_section('apache')
config.set('apache', 'sa_path', apache_sa_path)
config.set('apache', 'se_path', apache_se_path)

# postgresql connection configuration
config.add_section('odoo_db')
odoo_db_host = 'localhost'
_odoo_db_host = raw_input('Host[%s]: ' % odoo_db_host).strip()
if _odoo_db_host:
    odoo_db_host = _odoo_db_host
config.set('odoo_db', 'host', odoo_db_host)

odoo_db_port = 5432
_odoo_db_port = raw_input('Port No[%s]: ' % odoo_db_port).strip()
if _odoo_db_port:
    odoo_db_port = _odoo_db_port
config.set('odoo_db', 'port', odoo_db_port)

odoo_db_username = 'admin'
_odoo_db_username = raw_input('Username[%s]: ' % odoo_db_username).strip()
if _odoo_db_username:
    odoo_db_username = _odoo_db_username
config.set('odoo_db', 'username', odoo_db_username)

odoo_db_password = 'admin'
_odoo_db_password = getpass.getpass('Password[%s]: ' % odoo_db_password).strip()
if _odoo_db_password:
    odoo_db_password = _odoo_db_password
config.set('odoo_db', 'password', odoo_db_password)

# email configuration
config.add_section('email')

email_name = 'Sys Admin'
_email_name = raw_input('Name[%s]: ' % email_name).strip()
if _email_name:
    email_name = _email_name
config.set('email', 'name', email_name)

email_smtp_server = 'smtp.gmail.com'
_email_smtp_server = raw_input('SMTP Server[%s]: ' % email_smtp_server).strip()
if _email_smtp_server:
    email_smtp_server = _email_smtp_server
config.set('email', 'smtp', email_smtp_server)

email_username = 'axcensa@axcensa.com'
_email_username = raw_input('Username [%s]: ' % email_username).strip()
if _email_username:
    email_username = _email_username
config.set('email', 'username', email_username)

email_password = 'kqfijtzksnohugku'
_email_password = getpass.getpass('Password [%s]: ' % email_password).strip()
if _email_password:
    email_password = _email_password
config.set('email', 'password', email_password)

with open('%s/kutty.config' % config_home_path, 'wb') as configfile:
    config.write(configfile)
    print ">Configuration Setup Successfully<"

# copying certificate and key
cert_path = '%s/cert' % config_home_path
if os.path.isdir(cert_path):
    shutil.rmtree(cert_path)
shutil.copytree('setup/cert', '%s/cert' % config_home_path)
log_path = '%s/log' % config_home_path
os.mkdir(log_path)
print ">Server key and certificate files installed Successfully<"
print '\nPlease setup sudo user as nopassword sudo user'
print 'And setup postgresql user for kutty'
