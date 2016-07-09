import hashlib

import pymongo
from pymongo import MongoClient


class Activity:
    def __init__(self):
        pass

    def _first_deploy(self):
        self.con = MongoClient()
        if 'kutty' not in self.con.database_names():
            self.users = self.con['kutty']['users']
            self.users.create_index([('user', pymongo.ASCENDING)], unique=True)
            md5_password = hashlib.md5("password").hexdigest()
            self.users.insert_one({'user': 'admin', 'password': md5_password, 'type': 'admin', 'active': True,
                                   'name': 'Administrator', 'email': 'contactus@youcompany.com',
                                   'image': self._get_image()})
            self.odoo_instances = self.con['kutty']['odoo_instances']
            self.odoo_instances.create_index([('name', pymongo.ASCENDING)], unique=True)
        else:
            self.users = self.con['kutty']['users']
            self.odoo_instances = self.con['kutty']['odoo_instances']

    def _get_image(self):
        return 'data:image/png;base64,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'
