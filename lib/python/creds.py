import keyring

class EmptyKey(Exception): pass
class NullUserName(Exception): pass
class NullPassword(Exception): pass

class CredsHandler:
    """Retrieve username password from gnome keyring"""

    # EMCLI_USERNAME_KEY is usually the key

    def __init__(self, key):  # Initialize when created
        if not key:
            raise EmptyKey
        self.key = key                  # self is the new object
        self.service_id = 'emcli'

    def userName(self):
        return keyring.get_password(self.service_id, self.key)

    def getPassword(self, username):
        return keyring.get_password(self.service_id, username)
