import subprocess
import re 

def getcreds1(username, password):
    result = subprocess.run(['/usr/local/bin/getcreds'], stdout=subprocess.PIPE)

    m = re.match(r"username:(?P<username>\S+) password:(?P<password>\S+)", result.stdout.decode('utf-8'))

    if m:
        username[0] = m.group('username')
        password[0] = m.group('password')
    else:
        print('Cannot extract username/password from output')
        sys.exit(1)

# strings are immutable so we use a list
username = ['']
password = ['']
getcreds(username, password)

print('Username: ' + username[0])
print('Password: ' + password[0])

def getcreds2():
    result = subprocess.run(['/usr/local/bin/getcreds'], stdout=subprocess.PIPE)

    m = re.match(r"username:(?P<username>\S+) password:(?P<password>\S+)", result.stdout.decode('utf-8'))

    if m:
        return { 'username': m.group('username'), 'password': m.group('password') }
    else:
        print('Cannot extract username/password from output')
        sys.exit(1)

creds2 = getcreds2()

print('Username: ' + creds2['username'])
print('Password: ' + creds2['password'])

# for old pythons...
def getcreds3():
    result = subprocess.Popen(['/usr/local/bin/getcreds'], stdout=subprocess.PIPE).communicate()[0]

    m = re.match(r"username:(?P<username>\S+) password:(?P<password>\S+)", result.decode('utf-8'))

    if m:
        return { 'username': m.group('username'), 'password': m.group('password') }
    else:
        print('Cannot extract username/password from output')
        sys.exit(1)

creds3 = getcreds3()

print('Username: ' + creds3['username'])
print('Password: ' + creds3['password'])
