import sys
import argparse
# 'ConfigParser' has been renamed 'configparser' in Python 3 (Jython is ~ 2.7)
# In the latter case config[args.region]['url'] would be used instead of config.get(args.region, 'url')
# https://docs.python.org/2.7/library/configparser.html
import ConfigParser
from utils import getcreds
import json
import logging
from logging_ext import ColoredFormatter

parser = argparse.ArgumentParser(
    prog='generate_properties_config',
    description='Retrieve properties master lists',
    epilog='The .ini files found in @PKGDATADIR@ contain values for NODE (node.ini), REGION (region.ini)')

# Logging
log = logging.getLogger(parser.prog) # create top level logger

parser.add_argument('-L', '--logfile', type=argparse.FileType('a'), metavar='PATH', help='write logging to a file')
parser.add_argument('-V', '--loglevel', default='NOTICE', metavar='LEVEL',
    choices=['DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'CRITICAL'], help='console log level: %(choices)s')

# Region
config_region = ConfigParser.ConfigParser()
config_region.read('@PKGDATADIR@/region.ini')
group_oms = parser.add_mutually_exclusive_group(required=True)
group_oms.add_argument('-o', '--oms', help='URL for Enterprise Manager Console')
group_oms.add_argument('-r', '--region',
    choices=config_region.sections(), metavar='REGION', help='REGION: %(choices)s')

# Node
config_node = ConfigParser.ConfigParser()
config_node.read('@PKGDATADIR@/node.ini')
parser.add_argument('-n', '--node', required=True,
    choices=config_node.sections(), metavar='NODE', help='NODE: %(choices)s')

parser.add_argument('-u', '--username', help='OMS user, overides that found in @PKGDATADIR@/node.ini')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

if args.region:
    oms = config_region.get(args.region, 'url')
else:
    oms = args.oms

# Set up logging
numeric_level = getattr(logging, args.loglevel.upper(), None) # console log level
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)

ch = logging.StreamHandler() # add console handler 
ch.setLevel(numeric_level)
ch.setFormatter(ColoredFormatter("%(name)s[%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"))
log.addHandler(ch)

if args.logfile:
    fh = logging.FileHandler(args.logfile.name) # add file handler
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log.addHandler(fh)

log.setLevel(logging.NOTICE) # fallback log level (default WARNING)

log.notice('connecting to ' + oms)

# Set Connection properties and logon
set_client_property('EMCLI_OMS_URL', oms)
set_client_property('EMCLI_TRUSTALL', 'true')

if args.username:
    username = args.username
else:
    username = config_node.get(args.node, 'username')
# otherwise will atempt to obtain default username from getcreds()

if username:
    creds = getcreds(username)
else:
    creds = getcreds()
    username = creds['username']  # default username

if not username:
    print('Error: unable to determine username to use')
    sys.exit(1)

log.notice('username = ' + username)

login(username=username, password=creds['password'])

properties = ['Lifecycle Status', 'Cost Center', 'Department']

for property_name in properties:
    try:
        resp = list_target_properties_master_list_values(
            property_name = property_name )

    except emcli.exception.VerbExecutionError, e:
        log.error(e.error())
        exit(1)
       
    # Edit the header
    use_lambda = True
    # There are numerous ways to this. Turn the string (resp) which contains
    # newlines into a list using lambda to apply the formatting to the header or
    # pop() the first row (the header) from the list and edit and print it.

    if use_lambda: # Lambda
        resp_list = [(lambda x:'[' + x[x.rfind(': ', 1)+2:] + ']' if (':' in x) else x)(i) for i in resp.out().splitlines()]
    else: # Pop
        resp_list = resp.out().splitlines()

        header = resp_list.pop(0)
        print('[' + header[header.rfind(': ', 1)+2:] + ']') # header

    for item in resp_list:
        if len(item) > 0:
            print(item)

