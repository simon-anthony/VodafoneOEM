import sys
import argparse
# 'ConfigParser' has been renamed 'configparser' in Python 3 (Jython is ~ 2.7)
# In the latter case config[args.region]['url'] would be used instead of config.get(args.region, 'url')
# https://docs.python.org/2.7/library/configparser.html
import ConfigParser
from utils import getcreds

parser = argparse.ArgumentParser(
    prog='get_targets',
    description='Retrieve targets of specified type',
    epilog='Text at the bottom of help')

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

# target options
group_tgt = parser.add_mutually_exclusive_group()
group_tgt.add_argument('--host', action='store_true', help='Show agent target types (default)')
group_tgt.add_argument('--agent', action='store_true', help='Show host target types')
group_tgt.add_argument('--database', action='store_true', help='Show oracle database target types')
group_tgt.add_argument('--rac_database', action='store_true', help='Show RAC target types')
group_tgt.add_argument('--cluster', action='store_true', help='Show cluster target types')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

if args.region:
    oms = config_region.get(args.region, 'url')
else:
    oms = args.oms

print('Info: connecting to ' + oms)

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

# target_type can be oracle_emd, host, oracle_database etc....
target_type = 'host'
if args.agent:
    target_type = 'oracle_emd'
elif args.database:
    target_type = 'oracle_database'
elif args.rac_database:
    target_type = 'rac_database'
elif args.cluster:
    target_type = 'cluster'

# get_targets() returns:
#
# [ {'Host Info': 'host:oel.example.com;timezone_region:Europe/London',
#    'Target Type': 'oracle_database',
#    'Properties': 'Protocol:TCP;SID:FREE;MachineName:oel.example.com;OracleHome:/opt/oracle/product/dbhome;Port:1521',
#    'Associations': '',
#    'Target Name': 'FREE' }]
try:
    targets = get_targets(targets='%:'+target_type)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)
    
for target in targets.out()['data']:
    print target['Target Name']
