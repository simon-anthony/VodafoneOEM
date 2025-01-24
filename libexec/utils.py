# emcliext
import subprocess
import re 

class CredentialRetrieval(Exception): pass

def getcreds(username = None, hasrun = False):
    """Return username and password in a dict"""
    """ creds = getcreds() """
    """ print('Username: ' + creds['username']) """
    """ print('Password: ' + creds['password']) """

    if username:
        cmd = ['/usr/local/bin/getcreds', '-u', username]
    else:
        cmd = ['/usr/local/bin/getcreds']

    if hasrun:
        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        string = result.stdout.decode('utf-8')
    else: # for old pythons...
        result = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
        string = result.decode('utf-8')

    m = re.match(r"username:(?P<username>\S+) password:(?P<password>\S+)", string)

    if m:
        return { 'username': m.group('username'), 'password': m.group('password') }
    else:
        print('Cannot extract username/password from output')
        raise CredentialRetrieval()
