import sys
import argparse

parser = argparse.ArgumentParser(
    prog='submit_add_host',
    description='Install image on hosts',
    epilog='Text at the bottom of help')

# nargs=1 produces a list of 1 item, this differ from the default which produces the item itself
parser.add_argument('-o', '--oms', help='URL')
parser.add_argument('-u', '--username', default='SYSMAN', help='sysman user')
parser.add_argument('-p', '--password', required=True, help='sysman password')
# can also make gold image optional
parser.add_argument('-i', '--image', required=True, help='gold agent image name')
parser.add_argument('-b', '--base', default='/opt/oracle/product/13c/agent', help='installation base directory')
# Change credentials to default to OEM defaults
parser.add_argument('-c', '--credential', default='NC-ORACLE', help='credential name to login to host(s)')
parser.add_argument('-d', '--domain', help='default domain name if missing from host')
parser.add_argument('-w', '--wait', action='store_true', help='wait for completion')
parser.add_argument('host', nargs='+', help='list of host(s)')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

print('Connecting to: ' + args.oms)

platform = 226    # default, probably no other platforms than Linux
 
# Set Connection properties and logon
set_client_property('EMCLI_OMS_URL', args.oms)
set_client_property('EMCLI_TRUSTALL', 'true')
login(username=args.username, password=args.password)

# canonicalize host names if default domain available
if args.domain:
    host_names = [(lambda x:x+"."+args.domain if ("." not in x) else x)(i) for i in args.host]
else:
    host_names = args.host

# format for emcli
host_names = ';'.join(host_names)

try:
    resp = submit_add_host(
        host_names=host_names,
        platform=str(platform),
        installation_base_directory=args.base, 
        credential_name=args.credential,
        image_name=args.image)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

print resp
