import sys
import argparse
import re 

parser = argparse.ArgumentParser(
    prog='promote_discovered_targets',
    description='Promote discovered targets',
    epilog='Text at the bottom of help')

# nargs=1 produces a list of 1 item, this differ from the default which produces the item itself
parser.add_argument('-o', '--oms', help='URL')
parser.add_argument('-u', '--username', default='SYSMAN', help='sysman user')
parser.add_argument('-p', '--password', required=True, help='sysman password')
parser.add_argument('-m', '--monitor_pw', help='monitor password')

group = parser.add_mutually_exclusive_group()
group.add_argument('-a', '--all', action='store_true', help='Add all discovered Single Instance DBs')
group.add_argument('-t', '--target', nargs='+', help='Add only targets listed')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

if args.target:
    # extract the target names and create a ';' separated string from the list
    targetparms = ';'.join(i + ':oracle_database' for i in args.target)
elif args.all:
    targetparms = "oracle_database"
else:
    print 'Missing required arguments (-target or -all)'
    parser.print_help()
    sys.exit(2)

print('Connecting to: ' + args.oms)

# Set Connection properties and logon
set_client_property('EMCLI_OMS_URL', args.oms)
set_client_property('EMCLI_TRUSTALL', 'true')
login(username=args.username, password=args.password)

cred_str = "UserName:dbsnmp;password:" + args.monitor_pw + ";Role:Normal"

target_array = get_targets(unmanaged=True, properties=True, targets=targetparms).out()['data']

if len(target_array) == 0:
    print 'INFO: There are no targets to be promoted. Please verify the targets in Enterprise Manager webpages.'
    sys.exit(1)

for target in target_array:
    # The target['Host Info'] looks like host:oel.example.com;timezone_region:Europe/London
    m = re.match(r"host:(?P<host>\S+);.*", target['Host Info'])
    if m:
        host = m.group('host')
    else:
        print 'Cannot extract hostname from Host Info'
        sys.exit(1)

    try:
        print 'Adding target ' + target['Target Name'] + ' on ' + host
        #res1 = add_target(type='oracle_database', name=target['Target Name'], host=host, credentials=cred_str, properties=target['Properties'])
        print target['Target Name'] + " " + host + " " + target['Properties']
        print 'Succeeded'
    except VerbExecutionError, e:
        print 'Failed'
        print e.error()
        sys.exit(e.exit_code())
