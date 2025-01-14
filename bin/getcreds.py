#!/usr/bin/env python3

import vodafoneoem
import os

EMCLI_USERNAME_KEY = os.getenv('EMCLI_USERNAME_KEY')

mycreds = vodafoneoem.CredsHandler(EMCLI_USERNAME_KEY)

username = mycreds.userName()

if username:
    password = mycreds.getPassword(username)

    if password:
        print('username:' + username + ' password:' + password)
    else:
        print('ERROR: failed to retrieve password for "' + username + '"')
        sys.exit(1)
else:
    print('ERROR: failed to retrieve username')
    sys.exit(1)
