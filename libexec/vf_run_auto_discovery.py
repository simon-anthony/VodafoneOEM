import sys
import argparse
# 'ConfigParser' has been renamed 'configparser' in Python 3 (Jython is ~ 2.7)
# In the latter case config[args.region]['url'] would be used instead of config.get(args.region, 'url')
# https://docs.python.org/2.7/library/configparser.html
import ConfigParser
from utils import getcreds
import targets

parser = argparse.ArgumentParser(
    prog='run_auto_discovery',
    description='Run auto discovery on specified hosts',
    epilog='The .ini files found in @PKGDATADIR@ contain values for NODE (node.ini) and REGION (region.ini)')

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

parser.add_argument('-D', '--domain', help='default domain name if missing from host')
parser.add_argument('-w', '--wait', default=False, action='store_true', help='wait for completion')

# nargs=1 produces a list of 1 item, this differs from the default which produces the item itself
parser.add_argument('host', nargs='+', metavar='HOST', help='list of host(s)')

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

platform = '226'    # default, probably no other platforms than Linux

# Canonicalize host names if default domain available
if args.domain:
    host_list = [(lambda x:x+"."+args.domain if ("." not in x) else x)(i) for i in args.host]
else:
    host_list = args.host

# Host names format for emcli
host_names = ';'.join(host_list)
print('Info: auto discovery: ' + host_names)

try:
    resp = run_auto_discovery(
        host = host_names)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

print resp
