import sys
import argparse
# 'ConfigParser' has been renamed 'configparser' in Python 3 (Jython is ~ 2.7)
# In the latter case config[args.region]['url'] would be used instead of config.get(args.region, 'url')
# https://docs.python.org/2.7/library/configparser.html
import ConfigParser
from utils import getcreds
from utils import msg, msgLevel
import json

parser = argparse.ArgumentParser(
    prog='get_targets',
    description='Retrieve targets of specified type',
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

parser.add_argument('-u', '--username', help='OMS user, overides that found in @PKGDATADIR@/node.ini')
parser.add_argument('-D', '--domain', help='default domain name if missing from host(s) specified')
parser.add_argument('-U', '--unmanaged', default=False, action='store_true', help='get unmanaged targets (no status or alert information)')

group_output = parser.add_mutually_exclusive_group(required=False)
group_output.add_argument('-s', '--script', default=False, action='store_true', help='return output in script rather than JSON format)')
group_output.add_argument('-j', '--json', default=False, action='store_true', help='return complete output in JSON format)')

# target options
parser.add_argument('-t', '--type', '--target_type', default='host', 
    choices=['host', 'oracle_emd', 'oracle_database', 'oracle_home', 'rac_database', 'cluster'], metavar='TARGET_TYPE', 
    help='TARGET_TYPE: %(choices)s (default is host)')

# nargs=* gather zero or more args into a list
parser.add_argument('host', nargs='*', metavar='HOST', help='optional list of target(s)')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

if args.region:
    oms = config_region.get(args.region, 'url')
else:
    oms = args.oms

# Canonicalize host names if default domain available
if args.host:
    if args.domain:
        host_list = [(lambda x:x+"."+args.domain if ("." not in x) else x)(i) for i in args.host]
    else:
        host_list = args.host

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

# get_targets() returns:
#
# [ {'Host Info': 'host:oel.example.com;timezone_region:Europe/London',
#    'Target Type': 'oracle_database',
#    'Properties': 'Protocol:TCP;SID:FREE;MachineName:oel.example.com;OracleHome:/opt/oracle/product/dbhome;Port:1521',
#    'Associations': '',
#    'Target Name': 'FREE' }]

# Host names format for emcli
# By default, the separator_properties is ";" and the subseparator_properties is ":"
sep = ';'
subsep = ':'

if args.host:
    # targets format; targets = "[name1:]type1;[name2:]type2;..."
    if args.type == 'host' or args.type == 'rac_database':
        target_list = [(lambda x:x+subsep+args.type)(i) for i in host_list]
    elif args.type == 'oracle_home':
        target_list = [(lambda x:'%_'+x+'_%'+subsep+args.type)(i) for i in host_list]
    elif args.type == 'oracle_emd':
        target_list = [(lambda x:x+':3872'+subsep+args.type)(i) for i in host_list]
    targets = sep.join(target_list)
else:
    if args.unmanaged:
        targets = '%'
    else:
        targets = '%:' + args.type
msg(targets, level=msgLevel.INFO, tag='Targets')
try:
    resp = get_targets(
        targets = targets,
        script = args.script,
        unmanaged = args.unmanaged,
        properties = True if args.unmanaged else False,
        separator_properties = sep,
        subseparator_properties = subsep)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)
   
if resp.isJson():
    if args.json:
        print(json.dumps(resp.out(), indent=4))
    else:
        for target in resp.out()['data']:
            print(target['Target Type'] + ':' + target['Target Name'])
else:
    print(resp.out())
