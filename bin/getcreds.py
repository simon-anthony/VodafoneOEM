#!/usr/bin/env python3

import vodafoneoem
import os

EMCLI_USERNAME_KEY = os.getenv('EMCLI_USERNAME_KEY')

mycreds = vodafoneoem.CredsHandler(EMCLI_USERNAME_KEY)

username = mycreds.userName()

if username:
    password = mycreds.getPassword(username)

    if password:
        print('Username: ' + username)
        print('Password: ' + password)
    else:
        raise NullPassword
else:
    raise NullUserName

print('username:' + username + ' password:' + password)
