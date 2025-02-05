import sys
import argparse
# 'ConfigParser' has been renamed 'configparser' in Python 3 (Jython is ~ 2.7)
# In the latter case config[args.region]['url'] would be used instead of config.get(args.region, 'url')
# https://docs.python.org/2.7/library/configparser.html
import ConfigParser
from utils import getcreds
import json
import re

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
#parser.add_argument('-U', '--unmanaged', default=False, action='store_true', help='get unmanaged targets (no status or alert information)')

# target options
#parser.add_argument('-t', '--type', '--target_type', default='host', 
#    choices=['host', 'oracle_emd', 'oracle_database', 'oracle_home', 'rac_database', 'cluster', 'osm_cluster', 'has'], metavar='TARGET_TYPE', 
#    help='TARGET_TYPE: %(choices)s (default is host)')

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

print('Info: username = ' + username)

login(username=username, password=creds['password'])

# By default, the separator_properties is ";" and the subseparator_properties is ":"
sep = ';'
subsep = ':'

# Retrieve information about the cluster, not that only *one* node will be
# present in the 'Host Info'
targets = args.cluster + ':' + 'cluster'

try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

print(json.dumps(resp.out(), indent=4))

cluster = resp.out()['data'][0]['Target Name']  # there will be only one record
print('Info: cluster = ' + cluster)

m = re.match(r"host:(?P<host>\S+);", resp.out()['data'][0]['Host Info'])
if m:
    host = m.group('host')
else:
    print 'Error: cannot extract hostname from Host Info'
    sys.exit(1)

m = re.search(r"OracleHome:(?P<OracleHome>[^;]+).*scanName:(?P<scanName>[^;]+).*scanPort:(?P<scanPort>\d+)", resp.out()['data'][0]['Properties'])
if m:
    OracleHome = m.group('OracleHome')
    scanName = m.group('scanName')
    scanPort = m.group('scanPort')
else:
    print 'Error: cannot extract OracleHome/scanName/scanPort from Properties'
    sys.exit(1)

# Retrieve the full list of host members from the SCAN listeners

targets = 'LISTENER_SCAN%_' + cluster + ':oracle_listener'
try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

print(json.dumps(resp.out(), indent=4))

instances_list = []
for target in resp.out()['data']:   # multiple records
    m = re.match(r"host:(?P<host>\S+);", target['Host Info'])
    if m:
        instance = m.group('host')
        if instance not in instances_list:
            instances_list.append(host) 
    else:
        print 'Error: cannot extract hostname from Host Info'
        sys.exit(1)

instances_list = [(lambda x:x+':host')(i) for i in instances_list]
instances = ';'.join(instances_list)

print('Instances: '+ instances)


print('add_target -name='+ cluster + ' -type=cluster -host=' + host + ' -monitor_mode=1 -properties=OracleHome:' + OracleHome + ';scanName:' + scanName + ';scanPort:' + scanPort + ' -instances=' + instances)
