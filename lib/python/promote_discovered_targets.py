import sys
import argparse

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
group.add_argument('-t', '--targets', action='store_true', help='<target1:target2:...] Add only targets listed')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

print('Connecting to: ' + args.oms)

alltargets=False
targetparms=0

# Set Connection properties and logon
set_client_property('EMCLI_OMS_URL', args.oms)
set_client_property('EMCLI_TRUSTALL', 'true')
login(username=args.username, password=args.password)

cred_str = "UserName:dbsnmp;password:" + args.monitor_pw + ";Role:Normal"

if args.targets:
    targetparms = targetparms.replace(":",":oracle_database;") + ":oracle_database"
    target_array = get_targets(unmanaged=True, properties=True, targets=targetparms).out()['data']
elif args.all:
    target_array = get_targets(targets="oracle_database", unmanaged=True,properties=True ).out()['data']
else:
    print 'Missing required arguments (-targets or -all)'
    parser.print_help()
    sys.exit()

if len(target_array) > 0:
    for target in target_array:
        print 'Adding target ' + target['Target Name'] + '...',

        for host in str.split(target['Host Info'],";"):
            if host.split(":")[0] == "host":
                print host.split(":")[1]
        try:
            #res1 = add_target(type='oracle_database', name=target['Target Name'], host=host.split(":")[1], credentials=cred_str, properties=target['Properties'])
            #host=host.split(":")[1]
            #properties=target['Properties']
            print target['Target Name'] + " " + host.split(":")[1] + " " + target['Properties']
            print 'Succeeded'
        except VerbExecutionError, e:
            print 'Failed'
            print e.error()
            print 'Exit code:'+str(e.exit_code())
else:
    print 'INFO: There are no targets to be promoted. Please verify the targets in Enterprise Manager webpages.'
