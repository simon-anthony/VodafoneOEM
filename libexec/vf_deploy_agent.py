import sys
import argparse
import ConfigParser
from utils import getcreds
import targets
import re 
import logging
from logging_ext import ColoredFormatter

parser = argparse.ArgumentParser(
    prog='deploy_agent',
    description='Add agent to hosts with specified proprties',
    epilog='The .ini files found in @PKGDATADIR@ contain values for NODE (node.ini), REGION (region.ini) and STATUS, CENTER, DEPT (properties.ini). Values for STATUS, CENTER and DEPT must be quoted if they contain spaces')

# Logging
log = logging.getLogger(parser.prog) # create top level logger

parser.add_argument('-L', '--logfile', type=argparse.FileType('a'), metavar='PATH', help='write logging to a file')
parser.add_argument('-V', '--loglevel', default='NOTICE', metavar='LEVEL',
    choices=['DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'CRITICAL'], help='console log level')

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

# Make gold image optional
parser.add_argument('-i', '--image_name', default='agent_gold_image', help='agent gold image name, default \'%(default)s\'')
parser.add_argument('-B', '--installation_base_directory', help='installation base directory')
parser.add_argument('-I', '--instance_directory', help='instance directory')
parser.add_argument('-C', '--credential_name', help='credential name to login to host(s)')
parser.add_argument('-O', '--credential_owner', help='owner credential name to login to host(s)')
parser.add_argument('-D', '--domain', help='default domain name if missing from host')
parser.add_argument('-w', '--wait', default=False, action='store_true', help='wait for completion')
parser.add_argument('-x', '--exists_check', default=False, action='store_true', help='check if targets are already registered in OEM and quit if found')

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

# Canonicalize host names if default domain available
if args.domain:
    host_list = [(lambda x:x+"."+args.domain if ("." not in x) else x)(i) for i in args.host]
else:
    host_list = args.host

# Override or retrieve default values for the following settings:
settings_list = []

if args.credential_name:
    credential_name = args.credential_name
else:
    settings_list.append('credential_name')

if args.credential_owner:
    credential_owner = args.credential_owner
else:
    settings_list.append('credential_owner')

if args.installation_base_directory:
    installation_base_directory = args.installation_base_directory
else:
    settings_list.append('installation_base_directory')

if args.instance_directory:
    instance_directory = args.instance_directory
else:
    settings_list.append('instance_directory')
    
error = False
for lval in settings_list:
    try:
        str = lval + ' = ' + '"' + config_node.get(args.node, lval) + '"'
        log.info(str)
        exec(str)
    except ConfigParser.NoOptionError, e:
        log.error('no value for \'' + lval + '\' in section: \'' + args.node + '\'')
        error = True
if error:
    sys.exit(1)

# Set up logging
numeric_level = getattr(logging, args.loglevel.upper(), None) # console log level
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)

ch = logging.StreamHandler() # add console handler 
ch.setLevel(numeric_level)
ch.setFormatter(ColoredFormatter("%(name)s[%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"))
log.addHandler(ch)

if args.logfile:
    fh = logging.FileHandler(args.logfile.name) # add file handler
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log.addHandler(fh)

log.setLevel(logging.DEBUG) # fallback log (default WARNING)

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
    log.error('unable to determine username to use')
    sys.exit(1)

log.notice('username = ' + username)

login(username=username, password=creds['password'])

platform = '226'    # default, probably no other platforms than Linux

if args.exists_check:
    existing_targets = targets.TargetsList('host')   # list of host targets already in OEM

    existing_hosts = existing_targets.filterTargets(host_list)

    if (existing_hosts):
        log.error('the following hosts are already in OEM: ')
        for host in existing_hosts:
            print(host)
        sys.exit(1)


# Host names format for emcli
host_names = ';'.join(host_list)
log.info('adding: ' + host_names)

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
    log.error(e.error())
    exit(1)

print resp

if not args.wait:
    sys.exit(0)

# submit_add_host does not return JSON
m = re.search(r"^OverAll Status : (?P<status>.+)$", resp.out(), re.MULTILINE)
if m:
    status = m.group('status')
else:
    log.error('cannot extract status return')
    sys.exit(1)

log.notice('status is : ' + status)

if status != 'Agent Deployment Succeeded':
    sys.exit(1)

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
    log.error(e.error())
    exit(1)
