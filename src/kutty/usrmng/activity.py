import hashlib

import pymongo
from pymongo import MongoClient


class UserCredential:
    username = None
    password = None

    def __init__(self, username, password):
        self.username = username
        self.password = hashlib.md5(password).hexdigest()


class UserManagementActivity:
    def __init__(self):
        self.con = MongoClient()
        self._first_deploy()

    def _first_deploy(self):
        if 'kutty' not in self.con.database_names():
            self.users = self.con['kutty']['users']
            self.users.create_index([('user', pymongo.ASCENDING)], unique=True)
            md5_password = hashlib.md5("password").hexdigest()
            self.users.insert_one({'user': 'admin', 'password': md5_password, 'type': 'admin', 'active': True})
        else:
            self.users = self.con['kutty']['users']

    def _has_user_exits(self, username):
        if self.users.find({'user': username}).count() == 0:
            return False
        return True

    def adduser(self, username, password, type='normal'):
        if username == 'admin':
            raise UMException('Username - admin is not allowed')
        elif not self._has_user_exits(username):
            md5_password = hashlib.md5(password).hexdigest()
            self.users.insert_one({'user': username, 'password': md5_password, 'type': type, 'active': True})
        else:
            raise UMException('Username - %s is already exits' % username)

    def listuser(self):
        return self.users.find({}, {'user': 1, 'type': 1, 'active': 1})

    def activitate_user(self, username, active):
        if username == 'admin':
            raise UMException('Username - admin is not allowed')
        elif self._has_user_exits(username):
            self.users.update_one({'user': username}, {"$set": {'active': active}}, upsert=True)
        else:
            raise UMException('Username - %s is not exits' % username)

    def check_authentication(self, userCredential):
        if not isinstance(userCredential, UserCredential):
            raise UMException('Unsupported parameter found. Need UserCredential')
        if not self._has_user_exits(userCredential.username):
            raise UMException('Username - %s is not exits' % userCredential.username)
        else:
            if self.users.find({'user': userCredential.username, 'password': userCredential.password}).count() == 0:
                raise UMException('Username/password is mismatch')
        return True

    def deluser(self, username):
        self.users.remove({'user': username})

    def change_password(self, username, new_password):
        if not self._has_user_exits(username):
            raise UMException('Username - %s is not exits' % username)
        else:
            md5_password = hashlib.md5(new_password).hexdigest()
            self.users.update_one({'user': username}, {"$set": {'password': md5_password}}, upsert=True)


class UMException(Exception):
    pass
