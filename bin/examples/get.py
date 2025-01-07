# get.py
import keyring
import os

EMCLI_USERNAME_KEY = os.getenv('EMCLI_USERNAME_KEY')
service_id = 'emcli'

username = keyring.get_password(service_id, EMCLI_USERNAME_KEY)
password = keyring.get_password(service_id, username)

print('Username: ' + username)
print('Password: ' + password)
