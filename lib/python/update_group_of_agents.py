import sys
import argparse

parser = argparse.ArgumentParser(
    prog='update_group_of_agents',
    description='Update a group of agents',
    epilog='Text at the bottom of help')

# nargs=1 produces a list of 1 item, this differs from the default which produces the item itself
parser.add_argument('-o', '--oms', help='URL')
parser.add_argument('-u', '--username', default='SYSMAN', help='sysman user')
parser.add_argument('-p', '--password', required=True, help='sysman password')
parser.add_argument('-g', '--group', required=True, help='group')
parser.add_argument('-i', '--image', required=True, help='gold agent image name')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

print('Connecting to: ' + args.oms)
 
# Set Connection properties and logon
set_client_property('EMCLI_OMS_URL', args.oms)
set_client_property('EMCLI_TRUSTALL', 'true')
login(username=args.username, password=args.password)

# get all members of the specified group
try:
    members = get_group_members(name=args.group).out()['data']

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

# extract the target names and create a ';' separated string from the list
target_names = ','.join([i['Target Name'] for i in members if i['Target Type'] == 'oracle_emd']])

try:
    resp = update_agents(
        image_name=args.image,
        agents=target_names)

except emcli.exception.VerbExecutionError, e:
   print e.error()
   exit(1)

print resp
