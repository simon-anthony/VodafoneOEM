import sys
import argparse

parser = argparse.ArgumentParser(
    prog='create_group',
    description='Create a group from the given list of targets',
    epilog='Text at the bottom of help')

# nargs=1 produces a list of 1 item, this differ from the default which produces the item itself
parser.add_argument('-o', '--oms', default='oms.example.com', help='URL')
parser.add_argument('-u', '--username', default='SYSMAN', help='sysman user')
parser.add_argument('-p', '--password', required=True, help='sysman password')
parser.add_argument('-g', '--group', required=True, help='group')
parser.add_argument('-d', '--domain', help='default domain name if missing from host')
parser.add_argument('host', nargs='+', help='list of host(s)')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

print('Connecting to: ' + args.oms)
 
# Set Connection properties and logon
set_client_property('EMCLI_OMS_URL', args.oms)
set_client_property('EMCLI_TRUSTALL', 'true')
login(username=args.username, password=args.password)

# target_type can be oracle_emd, host, oracle_database etc....
target_type = "host"

# canonicalize host names if default domain available
if args.domain:
    targets = [(lambda x:x+"."+args.domain if ("." not in x) else x)(i) for i in args.host]
else:
    targets = args.host

# format for emcli
targets = ';'.join([s + ":" + target_type for s in targets])

try:
    resp = create_group(name=args.group, add_targets=targets)
except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)
    
print resp
