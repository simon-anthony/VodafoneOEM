import sys
import argparse
import ConfigParser
from utils import getcreds
import targets
import logging
import logging.config
from logging_ext import ColoredFormatter

parser = argparse.ArgumentParser(
    prog='run_auto_discovery',
    description='Run auto discovery on specified hosts',
    epilog='The .ini files found in @PKGDATADIR@ contain values for NODE (node.ini) and REGION (region.ini)')

# Logging
parser.add_argument('-L', '--logfile', type=argparse.FileType('a'), default='/dev/null',
    metavar='PATH', help='write logging to a file')
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
parser.add_argument('-D', '--domain', help='default domain name if missing from host')

# nargs=1 produces a list of 1 item, this differs from the default which produces the item itself
parser.add_argument('host', nargs='+', metavar='HOST', help='list of host(s)')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

if args.region:
    oms = config_region.get(args.region, 'url')
else:
    oms = args.oms

# Canonicalize host names if default domain available
if args.domain:
    host_list = [(lambda x:x+"."+args.domain if ("." not in x) else x)(i) for i in args.host]
else:
    host_list = args.host

# Set up logging
logging.config.fileConfig('@PKGDATADIR@/logging.conf', defaults={'logfilename': args.logfile.name})
log = logging.getLogger(parser.prog) # create top level logger

numeric_level = getattr(logging, args.loglevel.upper(), None) # console log level
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)
log.setLevel(numeric_level)

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

platform = '226'    # default, probably no other platforms than Linux

# Host names format for emcli
host_names = ';'.join(host_list)
log.notice('auto discovery: ' + host_names)

try:
    resp = run_auto_discovery(
        host = host_names)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

print resp
