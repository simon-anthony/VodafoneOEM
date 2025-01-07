import keyring

class CredsHandler:
    """Retrieve username password from gnome keyring"""

    # EMCLI_USERNAME_KEY is usually the key

    def __init__(self, key):  # Initialize when created
        self.key = key                  # self is the new object
        self.service_id = 'emcli'

    def userName(self):
        return keyring.get_password(self.service_id, self.key)

    def getPassword(self, username):
        return keyring.get_password(self.service_id, username)
