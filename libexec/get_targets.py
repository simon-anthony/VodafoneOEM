import sys
import argparse
import vodafoneoem
import os

parser = argparse.ArgumentParser(
    prog='get_targets',
    description='Retrieve targets of specified type',
    epilog='Text at the bottom of help')

# nargs=1 produces a list of 1 item, this differ from the default which produces the item itself
parser.add_argument('-o', '--oms', help='URL')
# parser.add_argument('-u', '--username', default='SYSMAN', help='sysman user')
# parser.add_argument('-p', '--password', required=True, help='sysman password')

group = parser.add_mutually_exclusive_group()
group.add_argument('--host', action='store_true', help='Show agent target types (default)')
group.add_argument('--agent', action='store_true', help='Show host target types')
group.add_argument('--database', action='store_true', help='Show oracle database target types')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

print('Connecting to: ' + args.oms)

platform=226    # default, probably no other platforms than Linux
 
# Set Connection properties and logon
set_client_property('EMCLI_OMS_URL', args.oms)
set_client_property('EMCLI_TRUSTALL', 'true')

EMCLI_USERNAME_KEY = os.getenv('EMCLI_USERNAME_KEY')

mycreds = vodafoneoem.CredsHandler(EMCLI_USERNAME_KEY)
username = mycreds.userName()
password = mycreds.getPassword(username)

login(username=username, password=password)

# target_type can be oracle_emd, host, oracle_database etc....
target_type = 'host'
if args.agent:
    target_type = 'oracle_emd'
elif args.database:
    target_type = 'oracle_database'

try:
    targets = get_targets(targets='%:'+target_type)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)
    
for target in targets.out()['data']:
    print target['Target Name']
