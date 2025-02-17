import sys
import argparse
# 'ConfigParser' has been renamed 'configparser' in Python 3 (Jython is ~ 2.7)
# In the latter case config[args.region]['url'] would be used instead of config.get(args.region, 'url')
# https://docs.python.org/2.7/library/configparser.html
import ConfigParser
from utils import getcreds

parser = argparse.ArgumentParser(
    prog='update_group_of_agents',
    description='Update a group of agents',
    epilog='The .ini files found in @PKGDATADIR@ contain values for NODE (node.ini), REGION (region.ini)')

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

# nargs=1 produces a list of 1 item, this differs from the default which produces the item itself
parser.add_argument('-u', '--username', help='OMS user, overides that found in @PKGDATADIR@/node.ini')
parser.add_argument('-g', '--group', required=True, help='group')
parser.add_argument('-i', '--image', required=True, help='gold agent image name')

group_sub = parser.add_mutually_exclusive_group(required=False)
group_sub.add_argument('-s', '--subscribe', action='store_true', default=False, help='subscribe to the gold image ')
group_sub.add_argument('-v', '--validate_only', action='store_true', default=False, help='check whether agents can be updated')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

if args.region:
    oms = config_region.get(args.region, 'url')
else:
    oms = args.oms

print('Info: connecting to: ' + oms)
 
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

print('Info: username = ' + username)

login(username=username, password=creds['password'])

# subscribe only
if args.subscribe:
    try:
        resp = subscribe_agents (
            image_name = args.image,
            groups = args.group)

    except emcli.exception.VerbExecutionError, e:
       print e.error()
       exit(1)

    print resp
    exit(0)

# get all members of the specified group
try:
    members = get_group_members(name=args.group).out()['data']

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

# extract the target names and create a ',' separated string from the list
target_names = ','.join([i['Target Name'] for i in members if i['Target Type'] == 'oracle_emd'])

try:
    resp = update_agents(
        image_name = args.image,
        agents = target_names,
        validate_only = args.validate_only)

except emcli.exception.VerbExecutionError, e:
   print e.error()
   exit(1)

print resp
