# emcliext
import subprocess
import re 

class CredentialRetrieval(Exception): pass

def getcreds(hasrun = None):
    """Return username and password in a dict"""
    """ creds = getcreds() """
    """ print('Username: ' + creds['username']) """
    """ print('Password: ' + creds['password']) """

    if hasrun:
        result = subprocess.run(['/usr/local/bin/getcreds'], stdout=subprocess.PIPE)
        string = result.stdout.decode('utf-8')
    else: # for old pythons...
        result = subprocess.Popen(['/usr/local/bin/getcreds'], stdout=subprocess.PIPE).communicate()[0]
        string = result.decode('utf-8')

    m = re.match(r"username:(?P<username>\S+) password:(?P<password>\S+)", string)

    if m:
        return { 'username': m.group('username'), 'password': m.group('password') }
    else:
        print('Cannot extract username/password from output')
        raise CredentialRetrieval()

