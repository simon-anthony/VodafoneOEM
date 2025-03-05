import sys
import argparse
import ConfigParser
from utils import getcreds
import json
import logging
import logging.config
from logging_ext import ColoredFormatter
from argparse_ext import CustomExtend

parser = argparse.ArgumentParser(
    prog='vf_generate_properties_config',
    description='Retrieve properties master lists',
    epilog='The .ini files found in @PKGDATADIR@ contain values for NODE (node.ini), REGION (region.ini)')

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

parser.add_argument('-p', '--property', nargs='+', action=CustomExtend, metavar='PROPERTY',
    default=['Lifecycle Status', 'Cost Center', 'Department'],
    defaultextended=False,
    help='list of properties, default is %(default)s')

parser.add_argument('-f', '--outfile', type=argparse.FileType('wb'), metavar='PATH', help='write config to file %(metavar)s')
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
    log.error('unable to determine username to use')
    sys.exit(1)

log.notice('username = ' + username)

login(username=username, password=creds['password'])

################################################################################

config = ConfigParser.RawConfigParser(allow_no_value=True)
config.optionxform = str # these values are to be case sensitive

for property_name in args.property:
    try:
        resp = list_target_properties_master_list_values(
            property_name = property_name )

    except emcli.exception.VerbExecutionError, e:
        log.error(e.error())
        exit(1)
       
    # There are numerous ways to do this. Turn the string (resp) which contains
    # newlines into a list using lambda to apply the formatting to the header or
    # pop() the first row (the header) from the list and edit and print it.

    if not args.outfile: # Lambda
        # edit the header (the line containing ': ')
        resp_list = [(lambda x:'[' + x[x.rfind(': ', 1)+2:] + ']' if (':' in x) else x)(i) for i in resp.out().splitlines()]

        for item in resp_list:
            if len(item) > 0:
                print(item)
        print('')

    else: # Pop
        resp_list = resp.out().splitlines()

        header = resp_list.pop(0) # pop first line
        section = header[header.rfind(': ', 1)+2:] # header
        config.add_section(section)

        for name in resp_list:
            if len(name) > 0:
                config.set(section, name)

if args.outfile: 
    config.write(args.outfile)

log.notice('properties written to ' + args.outfile.name)
