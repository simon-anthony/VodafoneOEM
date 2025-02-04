import sys
import argparse
# 'ConfigParser' has been renamed 'configparser' in Python 3 (Jython is ~ 2.7)
# In the latter case config[args.region]['url'] would be used instead of config.get(args.region, 'url')
# https://docs.python.org/2.7/library/configparser.html
import ConfigParser
from utils import getcreds

parser = argparse.ArgumentParser(
    prog='create_gold_agent_image',
    description='Create gold image from host',
    epilog='Quote DESCRIPTION if necessary')

# region
config_region = ConfigParser.ConfigParser()
config_region.read('@PKGDATADIR@/region.ini')
group_oms = parser.add_mutually_exclusive_group(required=True)
group_oms.add_argument('-o', '--oms', help='URL for Enterprise Manager Console')
group_oms.add_argument('-r', '--region',
    choices=config_region.sections(), metavar='REGION', help='REGION: %(choices)s')

# nargs=1 produces a list of 1 item, this differ from the default which produces the item itself
parser.add_argument('-v', '--version_name', required=True, help='source agent version name')
parser.add_argument('-i', '--image_name', required=True, help='gold agent image name')
parser.add_argument('-s', '--source_agent', required=True, help='source agent')
parser.add_argument('-p', '--port', default=3872, type=int, help='source agent port')
parser.add_argument('-d', '--description', help='source agent description')

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

creds = getcreds()
login(username=creds['username'], password=creds['password'])

try:
    resp = create_gold_agent_image(
        source_agent = args.source_agent + ':' + str(args.port),
        version_name = args.version_name,
        gold_image_description = args.description,
        image_name = args.image_name)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)
    
print('Info:' + resp.out())
