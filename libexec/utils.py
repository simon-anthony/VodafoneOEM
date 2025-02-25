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
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError

msgLevel = Enum(["ERROR", "WARNING", "INFO", "NOTICE", "USER", "NONE"])
msgColor = Enum(["BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE", "UNDERLINE", "BRIGHT_BLACK", "BRIGHT_RED", "BRIGHT_GREEN", "BRIGHT_YELLOW", "BRIGHT_BLUE", "BRIGHT_MAGENTA", "BRIGHT_CYAN", "BRIGHT_WHITE"])

def msg(s='', level=None, tag=None, color=None):
    """Format a message nicely"""

    if color:
        if color == msgColor.BLACK:
            ansicolor = style.BLACK
        elif color == msgColor.RED:
            ansicolor = style.RED
        elif color == msgColor.GREEN:
            ansicolor = style.GREEN
        elif color == msgColor.YELLOW:
            ansicolor = style.YELLOW
        elif color == msgColor.BLUE:
            ansicolor = style.BLUE
        elif color == msgColor.MAGENTA:
            ansicolor = style.MAGENTA
        elif color == msgColor.CYAN:
            ansicolor = style.CYAN
        elif color == msgColor.WHITE:
            ansicolor = style.WHITE
        elif color == msgColor.BRIGHT_BLACK:
            ansicolor = style.BRIGHT_BLACK
        elif color == msgColor.BRIGHT_RED:
            ansicolor = style.BRIGHT_RED
        elif color == msgColor.BRIGHT_GREEN:
            ansicolor = style.BRIGHT_GREEN
        elif color == msgColor.BRIGHT_YELLOW:
            ansicolor = style.BRIGHT_YELLOW
        elif color == msgColor.BRIGHT_BLUE:
            ansicolor = style.BRIGHT_BLUE
        elif color == msgColor.BRIGHT_MAGENTA:
            ansicolor = style.BRIGHT_MAGENTA
        elif color == msgColor.BRIGHT_CYAN:
            ansicolor = style.BRIGHT_CYAN
        elif color == msgColor.BRIGHT_WHITE:
            ansicolor = style.BRIGHT_WHITE
    else:
        if level == msgLevel.ERROR:
            ansicolor = style.RED
        elif level == msgLevel.WARNING:
            ansicolor = style.MAGENTA
        elif level == msgLevel.INFO:
            ansicolor = style.GREEN
        elif level == msgLevel.NOTICE:
            ansicolor = style.CYAN
        elif level == msgLevel.USER:
            ansicolor = style.BLUE
        else:
            ansicolor = None

    if not tag:
        if level == msgLevel.ERROR:
            tag = 'Error'
        elif level == msgLevel.WARNING:
            tag = 'Warning'
        elif level == msgLevel.INFO:
            tag = 'Info'
        elif level == msgLevel.NOTICE:
            tag = 'Notice'
        else:
            tag = None # :-) No default tag for msgLevel.USER

    prefix = ''
    suffix = ''

    if tag:
        if ansicolor:
            prefix = ansicolor + tag + style.RESET + ': '
        else:
            prefix =  tag + ': '
    else: # if not tag print the whole message in colour (if defined)
        if ansicolor:
            prefix = ansicolor
            suffix = style.RESET

    print(prefix + s + suffix)

