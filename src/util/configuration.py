import os

user_home = os.path.expanduser('~')


def get_home_path():
    return '%s/.kutty' % user_home


def find_config_file():
    return '%s/kutty.config' % get_home_path()


def find_cert_files():
    return '%s/cert/ssl.key' % get_home_path(), '%s/cert/ssl.cert' % get_home_path()


def find_log_files():
    return '%s/log/out.log' % get_home_path(), '%s/log/error.log' % get_home_path()
