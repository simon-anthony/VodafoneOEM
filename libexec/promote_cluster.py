from emcli.exception import VerbExecutionError
import sys
#from vf import *
import datetime as dt
import re 
import argparse
import csv

parser = argparse.ArgumentParser(
    prog='promote_cluster',
    description='Promote cluster',
    epilog='Text at the bottom of help')

# nargs=1 produces a list of 1 item, this differ from the default which produces the item itself
parser.add_argument('-o', '--oms', help='URL')
parser.add_argument('-u', '--username', default='SYSMAN', help='sysman user')
parser.add_argument('-p', '--password', required=True, help='sysman password')
parser.add_argument('-m', '--monitor_pw', help='monitor password')
parser.add_argument('-r', '--region', required=True, choices=['milan', 'dublin', 'rating'])

group = parser.add_mutually_exclusive_group()
group.add_argument('-a', '--all', action='store_true', help='Add all discovered Single Instance DBs')
group.add_argument('-t', '--target', nargs='+', help='Add only targets (hostnames) listed')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

if args.target:
    # extract the target names and create a ';' separated string from the list
    targetparms = ';'.join(i + ':oracle_database' for i in args.target)
elif args.all:
    targetparms="cluster"
else:
    print 'Missing required arguments (-targets or -all)'
    parser.print_help()
    sys.exit(2)

print('Connecting to: ' + args.oms)

# Set Connection properties and logon
set_client_property('EMCLI_OMS_URL', args.oms)
set_client_property('EMCLI_TRUSTALL', 'true')
login(username=args.username, password=args.password)
 
today=dt.datetime.now().strftime("%Y%m%d")
 
oem_urls = { 'dublin': 'https://vg00071de.snc5003.ie1ds014001oci1.oraclevcn.com:7799/em', 'milan': 'https://vg00011de.snc5003.it1ds014001oci1.oraclevcn.com:7799/em', 'rating' : 'https://vg00041de.snc5003.de1ds014001oci1.oraclevcn.com:7803/em'}
 
print("Info: adding clusters")
 
#Setup EMCLI environment
#set_url(region)
 
#Connect as dba_build
#conn_vf_dba_build()

cluster_file = '/tmp/cluster.csv'

def get_assocs(file, region, target):
    """Retrieve associations from given a region and target"""
    assocs = []
    with open(file) as csvfile:
        reader = csv.DictReader(csvfile, dialect='excel')
        for row in reader:
            if row['REGION'] == region and row['TARGET_NAME'] == target:
                assocs.append(row['ASSOC_TARGET_NAME'])
    return assocs

target_array = get_targets(unmanaged=True, properties=True, targets=targetparms).out()['data']

if len(target_array) == 0:
    print 'INFO: There are no targets to be promoted. Please verify the targets in Enterprise Manager webpages.'
    exit(1)

for target in target_array:
    cluster = target['Target Name']

    # The target['Host Info'] looks like host:oel.example.com;timezone_region:Europe/London
    m = re.match(r"host:(?P<host>\S+);.*", target['Host Info'])
    if m:
        host = m.group('host')
    else:
        print 'Cannot extract hostname from Host Info'
        sys.exit(1)

    properties = target['Properties']

    # Create ';' seprated string of instances
    instances = ';'.join(get_assocs(cluster_file, args.region, cluster))

    try:
        print 'Adding target cluster ' + cluster + ' for ' + host
        res = add_target(
            name=cluster,
            type='cluster',
            host=host,
            monitor_mode='1',
            properties=properties,
            instances=instances)
        print 'Succeeded'
    except VerbExecutionError, e:
        print 'Failed'
        print e.error()
        sys.exit(e.exit_code())
