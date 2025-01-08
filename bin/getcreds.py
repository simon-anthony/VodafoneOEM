#!/usr/bin/env python3

import vodafoneoem
import os

EMCLI_USERNAME_KEY = os.getenv('EMCLI_USERNAME_KEY')

mycreds = vodafoneoem.CredsHandler(EMCLI_USERNAME_KEY)

username = mycreds.userName()
password = mycreds.getPassword(username)

print('username:' + username + ' password:' + password)
