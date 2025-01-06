import keyring
#import os

def foo():
    print('XXXX!')

class CredsHandler:
    """Retrieve username password from gnome keyring"""

    #EMCLI_USERNAME_KEY = os.getenv('EMCLI_USERNAME_KEY')

    #def __init__(self, key, username):  # Initialize when created
    def __init__(self, key):  # Initialize when created
        self.key = key                  # self is the new object
        #self.username = username
        self.service_id = 'emcli'

    def userName(self):
        return keyring.get_password(self.service_id, self.key)

    def getPassword(self, username):
        return keyring.get_password(self.service_id, username)
