import sys
import argparse
import ConfigParser
from utils import getcreds
import logging
import logging.config
from logging_ext import ColoredFormatter

parser = argparse.ArgumentParser(
    prog='vf_create_gold_agent_image',
    description='Create gold image from host',
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

# nargs=1 produces a list of 1 item, this differ from the default which produces the item itself
parser.add_argument('-v', '--version_name', required=True, help='source agent version name')
parser.add_argument('-i', '--image_name', required=True, help='gold agent image name')
parser.add_argument('-s', '--source_agent', required=True, help='source agent')
parser.add_argument('-p', '--port', default=3872, type=int, help='source agent port')
parser.add_argument('-d', '--description', help='source agent description')
parser.add_argument('-u', '--username', help='OMS user, overides that found in @PKGDATADIR@/node.ini')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

if args.region:
    oms = config_region.get(args.region, 'url')
else:
    oms = args.oms

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

print('Info: username = ' + username)

login(username=username, password=creds['password'])

try:
    resp = create_gold_agent_image(
        source_agent = args.source_agent + ':' + str(args.port),
        version_name = args.version_name,
        gold_image_description = args.description,
        image_name = args.image_name)

except emcli.exception.VerbExecutionError, e:
    log.error(e.error())
    exit(1)
    
log.notice(resp.out())
