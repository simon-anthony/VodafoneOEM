import sys
import argparse
# 'ConfigParser' has been renamed 'configparser' in Python 3 (Jython is ~ 2.7)
# In the latter case config[args.region]['url'] would be used instead of config.get(args.region, 'url')
# https://docs.python.org/2.7/library/configparser.html
import ConfigParser
from utils import getcreds
import targets

parser = argparse.ArgumentParser(
    prog='deploy_agent',
    description='Add agent to hosts with specified proprties',
    epilog='The .ini files found in @PKGDATADIR@ contain values for NODE (node.ini), REGION (region.ini) amd STATUS, CENTER, DEPT (properties.ini). Values for STATUS, CENTER and DEPT must be quoted if they contain spaces')

# Region
config_region = ConfigParser.ConfigParser()
config_region.read('@PKGDATADIR@/region.ini')
group_oms = parser.add_mutually_exclusive_group()
group_oms.add_argument('-o', '--oms', help='URL for Enterprise Manager Console')
group_oms.add_argument('-r', '--region',
    choices=config_region.sections(), metavar='REGION', help='REGION: %(choices)s')

# Node
config_node = ConfigParser.ConfigParser()
config_node.read('@PKGDATADIR@/node.ini')
parser.add_argument('-n', '--node', required=True,
    choices=config_node.sections(), metavar='NODE', help='NODE: %(choices)s')

# Make gold image optional
parser.add_argument('-i', '--image_name', default='agent_gold_image', help='agent gold image name, default \'%(default)s\'')
parser.add_argument('-B', '--installation_base_directory', help='installation base directory')
parser.add_argument('-C', '--credential_name', help='credential name to login to host(s)')
parser.add_argument('-D', '--domain', help='default domain name if missing from host')
parser.add_argument('-w', '--wait', default=False, action='store_true', help='wait for completion')

# OEM properties
config_props = ConfigParser.ConfigParser(allow_no_value=True)
config_props.optionxform = str # these values are to be case sensitive
config_props.read('@PKGDATADIR@/properties.ini')

# These arguments can be known by different names.
# In this case, the first value starting with -- (normalized) is used in the arguments namespace.
parser.add_argument('-l', '--lifecycle_status', required=True,
    choices=config_props.options('Lifecycle Status'), metavar='STATUS', help='STATUS: %(choices)s')

parser.add_argument('-c', '--cost_center', '--bs_company', required=True,
    choices=config_props.options('Cost Center'), metavar='CENTER', help='CENTER: %(choices)s')

parser.add_argument('-d', '--department', '--support_group', required=True,
    choices=config_props.options('Department'), metavar='DEPT', help='DEPT: %(choices)s')

parser.add_argument('-b', '--line_of_business', '--bs_service', required=True,
    metavar='TEXT', help='TEXT is not constrained at present')

# nargs=1 produces a list of 1 item, this differs from the default which produces the item itself
parser.add_argument('host', nargs='+', metavar='HOST', help='list of host(s)')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

if args.region:
    oms = config_region.get(args.region, 'url')
else:
    oms = args.oms

error = False
for lval in ['credential_name', 'credential_owner', 'installation_base_directory', 'instance_directory']:
    try:
        str = lval + ' = ' + '"' + config_node.get(args.node, lval) + '"'
        print("Info: " + str)
        exec(str)
    except ConfigParser.NoOptionError, e:
        print('Error: no value for \'' + lval + '\' in section: \'' + args.node + '\'')
        error = True
if error:
    sys.exit(1)

if args.installation_base_directory:
    installation_base_directory = args.installation_base_directory

print('Info: connecting to ' + oms)

# Set Connection properties and logon
set_client_property('EMCLI_OMS_URL', oms)
set_client_property('EMCLI_TRUSTALL', 'true')

creds = getcreds()
login(username=creds['username'], password=creds['password'])

platform = '226'    # default, probably no other platforms than Linux

# canonicalize host names if default domain available
if args.domain:
    host_list = [(lambda x:x+"."+args.domain if ("." not in x) else x)(i) for i in args.host]
else:
    host_list = args.host

existing_targets = targets.TargetsList('host')   # list of host targets already in OEM

existing_hosts = existing_targets.filterTargets(host_list)

if (existing_hosts):
    print('Error: the following hosts are already in OEM: ' + existing_hosts)
    sys.exit(1)

# host names format for emcli
host_names = ';'.join(host_list)
print('Info: adding ' + host_names)

try:
    resp = submit_add_host(
        host_names = host_names,
        platform = platform,
        installation_base_directory = installation_base_directory,
        credential_name = credential_name,
        credential_owner = credential_owner,
        instance_directory = instance_directory,
        wait_for_completion = args.wait,
        image_name = args.image_name)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

print resp

if not args.wait:
    sys.exit(0)

# build up the property records: 
#    target_name:target_type:property_name:property_value[;target_name:target_type:property_name:property_value]...
property_records = []

for host in host_list:
    property_records.append(host + ':host:' + 'Lifecycle Status:' + args.lifecycle_status)
    property_records.append(host + ':host:' + 'Cost Center:' + args.cost_center)
    property_records.append(host + ':host:' + 'Department:' + args.department)
    property_records.append(host + ':host:' + 'Line of Business:' + args.line_of_business)
property_records = ';'.join(property_records)

try:
    resp = set_target_property_value(
        property_records = property_records)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)
