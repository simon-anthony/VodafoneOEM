# emcliext
import subprocess
import re 

class CredentialRetrieval(Exception): pass

def getcreds():
    """Return username and password in a dict"""
    """ creds = getcreds() """
    """ print('Username: ' + creds['username']) """
    """ print('Password: ' + creds['password']) """

    result = subprocess.run(['/usr/local/bin/getcreds'], stdout=subprocess.PIPE)

    m = re.match(r"username:(?P<username>\S+) password:(?P<password>\S+)", result.stdout.decode('utf-8'))

    if m:
        return { 'username': m.group('username'), 'password': m.group('password') }
    else:
        print('Cannot extract username/password from output')
        raise CredentialRetrieval()
        #sys.exit(1)

# for old pythons...
def getcreds_legacy():
    result = subprocess.Popen(['/usr/local/bin/getcreds'], stdout=subprocess.PIPE).communicate()[0]

    m = re.match(r"username:(?P<username>\S+) password:(?P<password>\S+)", result.decode('utf-8'))

    if m:
        return { 'username': m.group('username'), 'password': m.group('password') }
    else:
        print('Cannot extract username/password from output')
        raise CredentialRetrieval()
        #sys.exit(1)
