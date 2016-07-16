import base64
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
        with open("kutty_logo.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            return encoded_string
        return ""
