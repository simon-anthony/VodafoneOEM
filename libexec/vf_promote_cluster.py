import sys
import argparse
# 'ConfigParser' has been renamed 'configparser' in Python 3 (Jython is ~ 2.7)
# In the latter case config[args.region]['url'] would be used instead of config.get(args.region, 'url')
# https://docs.python.org/2.7/library/configparser.html
import ConfigParser
from utils import getcreds
from utils import msg
import json
import re
debug = True

parser = argparse.ArgumentParser(
    prog='promote_cluster',
    description='Promote a clustser after discovery',
    epilog='The .ini files found in /usr/local/share/vodafoneoem contain values for NODE (node.ini), REGION (region.ini)')

# Region
config_region = ConfigParser.ConfigParser()
config_region.read('/usr/local/share/vodafoneoem/region.ini')
group_oms = parser.add_mutually_exclusive_group(required=True)
group_oms.add_argument('-o', '--oms', help='URL for Enterprise Manager Console')
group_oms.add_argument('-r', '--region',
    choices=config_region.sections(), metavar='REGION', help='REGION: %(choices)s')

# Node
config_node = ConfigParser.ConfigParser()
config_node.read('/usr/local/share/vodafoneoem/node.ini')
parser.add_argument('-n', '--node', required=True,
    choices=config_node.sections(), metavar='NODE', help='NODE: %(choices)s')
parser.add_argument('-u', '--username', help='OMS user, overides that found in /usr/local/share/vodafoneoem/node.ini')

# only one positional argument - the cluster
parser.add_argument('cluster', metavar='CLUSTER', help='name of cluster')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

if args.region:
    oms = config_region.get(args.region, 'url')
else:
    oms = args.oms

print('Info: connecting to ' + oms)

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
    print('Error: unable to determine username to use')
    sys.exit(1)

msg('username = ' + username, 'info')

login(username=username, password=creds['password'])

# Retrieve information about the cluster, note that only *one* node will be
# present in the 'Host Info' (the last one to be discovered)
targets = args.cluster + ':' + 'cluster'

try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

if len(resp.out()['data']) == 0:
    print('Error: no such cluster ' + args.cluster)
    sys.exit(1)

# 1911671.1 How to add Cluster ASM Target
# 1908635.1 How to Discover the Cluster and Cluster Database (RAC) Target

################################################################################
# 1. Add the Cluster Target
################################################################################
if debug:
    print(json.dumps(resp.out(), indent=4))

####
# i. Add the cluster (cluster) target
####

cluster = resp.out()['data'][0]['Target Name']  # there will be only one record

m = re.match(r"host:(?P<host>\S+);", resp.out()['data'][0]['Host Info'])
if m:
    host = m.group('host')
else:
    print('Error: cannot extract hostname from Host Info')
    sys.exit(1)

m = re.search(r"OracleHome:(?P<OracleHome>[^;]+).*scanName:(?P<scanName>[^;]+).*scanPort:(?P<scanPort>\d+)", resp.out()['data'][0]['Properties'])
if m:
    OracleHome = m.group('OracleHome')
    scanName = m.group('scanName')
    scanPort = m.group('scanPort')
else:
    print('Error: cannot extract OracleHome/scanName/scanPort from Properties')
    sys.exit(1)

# Retrieve the full list of host members from the SCAN listeners
targets = 'LISTENER_SCAN%_' + cluster + ':oracle_listener'
try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

if debug: 
    print(json.dumps(resp.out(), indent=4))

instances_list = []
for target in resp.out()['data']:   # multiple records
    m = re.match(r"host:(?P<host>\S+);", target['Host Info'])
    if m:
        instance = m.group('host')
        m = re.search(r"Machine:(?P<Machine>[^;]+)", resp.out()['data'][0]['Properties'])
        if m:
            Machine = m.group('Machine')
            if Machine == scanName: # check Machine matches scanName, otherwise ignore
                if instance not in instances_list:
                    instances_list.append(instance) 
        else:
            print 'Error: cannot extract MachineName from Properties'
    else:
        print 'Error: cannot extract hostname from Host Info'
        sys.exit(1)

instances = ';'.join([(lambda x:x+':host')(i) for i in instances_list])

msg(instances, level='info', tag='Instances')

print('add_target -name='+ cluster + ' -type=cluster -host=' + host + ' -monitor_mode=1 -properties=OracleHome:' + OracleHome + ';scanName:' + scanName + ';scanPort:' + scanPort + ' -instances=' + instances)

####
#  ii. Add the database instance (oracle_database) targets
# iii. Add the remainig nodes
####
# Assume only DBs on instance are for cluster

targets = 'oracle_database'
try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

hosts_list = []
for target in resp.out()['data']:   # multiple records
    m = re.match(r"host:(?P<host>\S+);", target['Host Info'])
    if m:
        host = m.group('host')
        msg(host, level='info', tag='Checking')
        if host in instances_list: # check host is one of our instances, otherwise ignore
            hosts_list.append(host) 
            m = re.search(r"SID:(?P<SID>[^;]+).*MachineName:(?P<MachineName>[^;]+).*OracleHome:(?P<OracleHome>[^;]+).*Port:(?P<Port>[^;]+).*ServiceName:(?P<ServiceName>[^;]+)", target['Properties'])
            if m:
                SID = m.group('SID')
                MachineName = m.group('MachineName')
                OracleHome = m.group('OracleHome')
                Port = m.group('Port')
                ServiceName = m.group('ServiceName')

                print('add_target -name='+ target['Target Name'] + ' -type=oracle_database -host=' + host + ' -monitor_mode=1 -properties="SID:'+SID+';Port:'+Port+';OracleHome:'+OracleHome+';MachineName:'+MachineName+'"')
            else:
                print('Error: cannot extract OracleHome/scanName/scanPort from Properties')
                sys.exit(1)
    else:
        print('Error: cannot extract hostname from Host Info')
        sys.exit(1)

if debug: 
    print(json.dumps(resp.out(), indent=4))

####
#  iv. Add the Cluster database (rac_database) target
####


#
# 2) Add the ASM Instance Targets
#

