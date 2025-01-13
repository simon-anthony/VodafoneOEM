from emcli.exception import VerbExecutionError
import sys
#from vf import *
import datetime as dt
import re 
import argparse
import csv
import ConfigParser
from utils import getcreds

parser = argparse.ArgumentParser(
    prog='promote_cluster',
    description='Promote cluster',
    epilog='Text at the bottom of help')

parser.add_argument('-m', '--monitor_pw', help='monitor password')
parser.add_argument('-c', '--csv', help='CSV file containing targets')

# target options
group_tgt = parser.add_mutually_exclusive_group()
group_tgt.add_argument('-a', '--all', action='store_true', help='Add all discovered Single Instance DBs')
group_tgt.add_argument('-t', '--target', nargs='+', help='Add only targets (hostnames) listed')

# OMS options
config = ConfigParser.ConfigParser()
config.read('@PKGDATADIR@/oms.ini')

group_oms = parser.add_mutually_exclusive_group()
group_oms.add_argument('-o', '--oms', help='URL')
group_oms.add_argument('-r', '--region', choices=config.sections())

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

if args.target:
    # extract the target names and create a ';' separated string from the list
    targetparms = ';'.join(i + ':oracle_database' for i in args.target)
elif args.all:
    targetparms="cluster"

if args.region:
    oms = config.get(args.region, 'url')
else:
    oms = args.oms

print('Connecting to: ' + oms)

# Set Connection properties and logon
set_client_property('EMCLI_OMS_URL', oms)
set_client_property('EMCLI_TRUSTALL', 'true')

creds = getcreds()
login(username=creds['username'], password=creds['password'])
 
today = dt.datetime.now().strftime("%Y%m%d")
 
print("INFO: adding clusters")
 
if args,csv:
    cluster_file = args.csv
else:
    cluster_file = '@PKGDATADIR@/cluster.csv'

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
        print 'ERROR: Cannot extract hostname from Host Info'
        sys.exit(1)

    properties = target['Properties']

    # Create ';' seprated string of instances
    instances = ';'.join(get_assocs(cluster_file, args.region, cluster))

    try:
        print 'INFO: Adding target cluster ' + cluster + ' for ' + host
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
