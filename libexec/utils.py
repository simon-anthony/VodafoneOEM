# emcliext
import subprocess
import re 
import sys 

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

class style():
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

def msg(s='', level=None, tag=None, color=None):
    """Format a message nicely"""

    # Jython does not like: print(s, file=sys.stderr), so we have to write to
    # stderr
    if color:
        if color.upper() == BLACK:
            ansicolor = style.BLACK
        if color.upper() == RED:
            ansicolor = style.RED
        if color.upper() == GREEN:
            ansicolor = style.GREEN
        if color.upper() == YELLOW:
            ansicolor = style.YELLOW
        if color.upper() == BLUE:
            ansicolor = style.BLUE
        if color.upper() == MAGENTA:
            ansicolor = style.MAGENTA
        if color.upper() == CYAN:
            ansicolor = style.CYAN
        if color.upper() == WHITE:
            ansicolor = style.WHITE
    else:
        if level.lower() == 'error':
            ansicolor = style.RED
        elif level.lower() == 'warning':
            ansicolor = style.YELLOW
        elif level.lower() == 'info':
            ansicolor = style.GREEN
        else:
            ansicolor = None

    if not tag:
        if level.lower() == 'error':
            tag = 'Error'
        elif level.lower() == 'warning':
            tag = 'Warning'
        elif level.lower() == 'info':
            tag = 'Info'
        else:
            tag = None
    if tag:
        prefix = ansicolor + tag + style.RESET + ': '
    else:
        prefix = ''

    print(prefix + s)
