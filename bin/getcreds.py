#!/usr/bin/python3

import vodafoneoem
import os
import sys
import argparse

parser = argparse.ArgumentParser(
    prog='getcreds',
    description='Retrieve given credentials for username or default EMCLI_USERNAME_KEY')

parser.add_argument('-u', '--username', help='username otherwise get from env')

args = parser.parse_args()

# if username is not provided lookup the default from EMCLI_USERNAME_KEY

if args.username:
    username = args.username
    mycreds = vodafoneoem.CredsHandler(username)

else:
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
