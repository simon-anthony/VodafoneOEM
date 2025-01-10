import sys
import argparse
# 'ConfigParser' has been renamed 'configparser' in Python 3 (Jython is ~ 2.7)
# One would the refer to config[args.region]['url'] instead of config.get(args.region, 'url')
import ConfigParser
from utils import getcreds

parser = argparse.ArgumentParser(
    prog='get_targets',
    description='Retrieve targets of specified type',
    epilog='Text at the bottom of help')

# nargs=1 produces a list of 1 item, this differ from the default which produces the item itself

# target options
group_tgt = parser.add_mutually_exclusive_group()
group_tgt.add_argument('--host', action='store_true', help='Show agent target types (default)')
group_tgt.add_argument('--agent', action='store_true', help='Show host target types')
group_tgt.add_argument('--database', action='store_true', help='Show oracle database target types')

# OMS options
config = ConfigParser.ConfigParser()
config.read('@PKGDATADIR@/oms.ini')

group_oms = parser.add_mutually_exclusive_group()
group_oms.add_argument('-o', '--oms', help='URL')
group_oms.add_argument('-r', '--region', choices=config.sections())

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

if args.region:
    oms = config.get(args.region, 'url')
else:
    oms = args.oms

print('Connecting to: ' + oms)

platform=226    # default, probably no other platforms than Linux
 
# Set Connection properties and logon
set_client_property('EMCLI_OMS_URL', oms)
set_client_property('EMCLI_TRUSTALL', 'true')

creds = getcreds()
login(username=creds['username'], password=creds['password'])

# target_type can be oracle_emd, host, oracle_database etc....
target_type = 'host'
if args.agent:
    target_type = 'oracle_emd'
elif args.database:
    target_type = 'oracle_database'

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
