import sys
import argparse
# 'ConfigParser' has been renamed 'configparser' in Python 3 (Jython is ~ 2.7)
# In the latter case config[args.region]['url'] would be used instead of config.get(args.region, 'url')
# https://docs.python.org/2.7/library/configparser.html
import ConfigParser
from utils import getcreds

parser = argparse.ArgumentParser(
    prog='promote_gold_agent_image',
    description='Promote gold image from',
    epilog='Text at the bottom of help')

# region
config_region = ConfigParser.ConfigParser()
config_region.read('@PKGDATADIR@/region.ini')
group_oms = parser.add_mutually_exclusive_group()
group_oms.add_argument('-o', '--oms', help='URL for Enterprise Manager Console')
group_oms.add_argument('-r', '--region',
    choices=config_region.sections(), metavar='REGION', help='REGION: %(choices)s')

# nargs=1 produces a list of 1 item, this differ from the default which produces the item itself
parser.add_argument('-v', '--version', required=True, help='gold image version name')
parser.add_argument('-m', '--maturity', choices=['Current', 'Restricted', 'Draft'], default='Current',
    help='set maturity, default: %(default)s')

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
    resp = promote_gold_agent_image(
        version_name=args.version,
        maturity=args.maturity)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)
    
print resp
