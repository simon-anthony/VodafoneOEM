import sys
import argparse

parser = argparse.ArgumentParser(
    prog='create_gold_agent_image',
    description='Create gold image from host',
    epilog='Text at the bottom of help')

# nargs=1 produces a list of 1 item, this differ from the default which produces the item itself
parser.add_argument('-o', '--oms', help='URL')
parser.add_argument('-u', '--username', default='SYSMAN', help='sysman user')
parser.add_argument('-p', '--password', required=True, help='sysman password')
parser.add_argument('-v', '--version', required=True, help='gold image version name')
parser.add_argument('-m', '--maturity', default='Current', help='source agent description')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

print('Connecting to: ' + args.oms)

# Set Connection properties and logon
set_client_property('EMCLI_OMS_URL', args.oms)
set_client_property('EMCLI_TRUSTALL', 'true')
login(username=args.username, password=args.password)

try:
    resp = promote_gold_agent_image(
        version_name=args.version,
        maturity=args.maturity)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)
    
print resp
