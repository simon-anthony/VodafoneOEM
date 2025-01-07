# put.py
import keyring
import os

EMCLI_USERNAME_KEY = os.getenv('EMCLI_USERNAME_KEY')
service_id = 'emcli'
username = 'sysman'
password = 'Naxy7839'

keyring.set_password(service_id, username, password)
keyring.set_password(service_id, EMCLI_USERNAME_KEY, username)
