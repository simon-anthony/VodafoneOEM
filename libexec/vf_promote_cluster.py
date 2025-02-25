import sys
import argparse
import ConfigParser
from utils import getcreds
from utils import msg, msgLevel
import json
import re
debug = True

parser = argparse.ArgumentParser(
    prog='promote_cluster',
    description='Promote a clustser after discovery',
    epilog='The .ini files found in @PKGDATADIR@ contain values for NODE (node.ini), REGION (region.ini)')

# Region
config_region = ConfigParser.ConfigParser()
config_region.read('@PKGDATADIR@/region.ini')
group_oms = parser.add_mutually_exclusive_group(required=True)
group_oms.add_argument('-o', '--oms', help='URL for Enterprise Manager Console')
group_oms.add_argument('-r', '--region',
    choices=config_region.sections(), metavar='REGION', help='REGION: %(choices)s')

# Node
config_node = ConfigParser.ConfigParser()
config_node.read('@PKGDATADIR@/node.ini')
parser.add_argument('-n', '--node', required=True,
    choices=config_node.sections(), metavar='NODE', help='NODE: %(choices)s')
parser.add_argument('-u', '--username', help='OMS user, overides that found in @PKGDATADIR@/node.ini')
parser.add_argument('-s', '--dbsnmpuser', help='SNMP user, overides that found in @PKGDATADIR@/node.ini')

# only one positional argument - the cluster
parser.add_argument('cluster', metavar='CLUSTER', help='name of cluster')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

if args.region:
    oms = config_region.get(args.region, 'url')
else:
    oms = args.oms

msg('connecting to ' + oms, msgLevel.INFO)

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
    msg('unable to determine username to use', msgLevel.ERROR)
    sys.exit(1)

msg('username = ' + username, msgLevel.INFO)

login(username=username, password=creds['password'])

# retrieve dbsnmp password
if args.dbsnmpuser:
    dbsnmpuser = args.dbsnmpuser
else:
    dbsnmpuser = config_node.get(args.node, 'dbsnmpuser')

if not dbsnmpuser:
    msg('unable to determine username for DB snmp', msgLevel.ERROR)
    sys.exit(1)

dbsnmpcreds = getcreds(dbsnmpuser)
dbsnmppass = dbsnmpcreds['password']

msg('DB SNMP username = ' + dbsnmpuser, msgLevel.INFO)

# Retrieve information about the cluster, note that only *one* node will be
# present in the 'Host Info' (the last one to be discovered)
targets = args.cluster + ':' + 'cluster'

try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

if len(resp.out()['data']) == 0:
    msg('no such cluster ' + args.cluster, msgLevel.ERROR)
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
msg(cluster, level=msgLevel.INFO, tag='Cluster')

m = re.match(r"host:(?P<host>\S+);", resp.out()['data'][0]['Host Info'])
if m:
    host = m.group('host')
else:
    msg('cannot extract hostname from Host Info', msgLevel.ERROR)
    sys.exit(1)

m = re.search(r"OracleHome:(?P<OracleHome>[^;]+).*scanName:(?P<scanName>[^;]+).*scanPort:(?P<scanPort>\d+)", resp.out()['data'][0]['Properties'])
if m:
    OracleHome = m.group('OracleHome')
    scanName = m.group('scanName')
    scanPort = m.group('scanPort')
else:
    msg('cannot extract OracleHome/scanName/scanPort from Properties', msgLevel.ERROR)
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
                if instance not in instances_list: # avoid duplication
                    instances_list.append(instance) 
        else:
            msg('cannot extract MachineName from Properties', msgLevel.ERROR)
    else:
        msg('cannot extract hostname from Host Info', msgLevel.ERROR)
        sys.exit(1)

instances = ';'.join([(lambda x:x+':host')(i) for i in instances_list])

msg(instances, level=msgLevel.INFO, tag='Instances')

msg('add_target -name='+ cluster + ' -type=cluster -host=' + host + ' -monitor_mode=1 -properties=OracleHome:' + OracleHome + ';scanName:' + scanName + ';scanPort:' + scanPort + ' -instances=' + instances, msgLevel.USER, tag='EMCLI')

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

dbs_list = [] # needed for the targets to add to rac_database
for target in resp.out()['data']:   # multiple records
    m = re.match(r"host:(?P<host>\S+);", target['Host Info'])
    if m:
        host = m.group('host')
        msg(host, level=msgLevel.INFO, tag='Oracle Database')
        if host in instances_list: # check host is one of our instances, otherwise ignore
            dbs_list.append(target['Target Name']) 
            m = re.search(r"SID:(?P<SID>[^;]+).*MachineName:(?P<MachineName>[^;]+).*OracleHome:(?P<OracleHome>[^;]+).*Port:(?P<Port>[^;]+).*ServiceName:(?P<ServiceName>[^;]+)", target['Properties'])
            if m:
                SID = m.group('SID')
                MachineName = m.group('MachineName')
                OracleHome = m.group('OracleHome')
                Port = m.group('Port')
                ServiceName = m.group('ServiceName')

                msg('add_target -name='+ target['Target Name'] +
                ' -type=oracle_database' +
                ' -host=' + host +
                ' -credentials="UserName:' + dbsnmpuser + ';password=' + dbsnmppass + ';Role:Normal"' +
                ' -properties="SID:'+SID+';Port:'+Port+';OracleHome:'+OracleHome+';MachineName:'+MachineName+'"', msgLevel.USER, tag='EMCLI')
            else:
                msg('cannot extract SID/MachineName/OracleHome/Port/ServiceName from Properties', msgLevel.ERROR)
                sys.exit(1)
    else:
        msg('cannot extract hostname from Host Info', msgLevel.ERROR)
        sys.exit(1)

if debug: 
    print(json.dumps(resp.out(), indent=4))

####
#  iv. Add the Cluster database (rac_database) target
####
# Find the rac_database with ServiceName the same as the oracle_databases
# Only one record per rac_database will be returned...

msg('looking for rac_database ' + ServiceName, msgLevel.INFO)

targets = 'rac_database'
try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

for target in resp.out()['data']:   # multiple records
    if target['Target Name'] != ServiceName:  
        continue
    # got it!

    m = re.match(r"host:(?P<host>\S+);", target['Host Info'])
    if m:
        host = m.group('host')
    else:
        msg('cannot extract hostname from Host Info', msgLevel.ERROR)
        sys.exit(1)

    m = re.search(r"ClusterName:(?P<ClusterName>[^;]+).*ServiceName:(?P<ServiceName>[^;]+)", target['Properties'])
    if m:
        ClusterName = m.group('ClusterName')
        ServiceName = m.group('ServiceName')
    else:
        msg('cannot extract ClusterName/ServiceName from Properties', msgLevel.ERROR)
        sys.exit(1)

    instances = ';'.join([(lambda x:x+':oracle_database')(i) for i in dbs_list])

    msg(ServiceName, level=msgLevel.INFO, tag='RAC Database')
    msg('add_target -name=' + target['Target Name'] +
        ' -type=rac_database -host=' + host +
        ' -monitor_mode=1 -properties="ServiceName:'+ServiceName+';ClusterName:'+ClusterName+'" -instances="'+instances+'"', msgLevel.USER, tag='EMCLI')


################################################################################
# 2) Add the ASM Instance Targets
################################################################################

msg('looking for ASM instances on ' + ' '.join(instances_list), msgLevel.INFO)

targets = 'osm_instance'
try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

osm_list = [] # needed for the targets to add to osm_cluster
for target in resp.out()['data']:   # multiple records
    m = re.match(r"host:(?P<host>\S+);", target['Host Info'])
    if m:
        host = m.group('host')
        msg(host, level=msgLevel.INFO, tag='ASM Instance')
        if host in instances_list: # check host is one of our instances, otherwise ignore
            osm_list.append(target['Target Name']) 
            m = re.search(r"MachineName:(?P<MachineName>[^;]+).*OracleHome:(?P<OracleHome>[^;]+).*Port:(?P<Port>[^;]+).*SID:(?P<SID>[^;]+)", target['Properties'])
            if m:
                MachineName = m.group('MachineName')
                OracleHome = m.group('OracleHome')
                Port = m.group('Port')
                SID = m.group('SID')

                msg('add_target -name='+ target['Target Name'] +
                ' -type=osm_instance' +
                ' -host=' + host +
                ' -credentials="UserName:' + dbsnmpuser + ';password=' + dbsnmppass + ';Role:sysdba"' +
                ' -properties="SID:'+SID+';Port:'+Port+';OracleHome:'+OracleHome+';MachineName:'+MachineName+'"', msgLevel.USER, tag='EMCLI')
            else:
                msg('cannot extract MachineName/OracleHome/Port/SID from Properties', msgLevel.ERROR)
                sys.exit(1)
    else:
        msg('cannot extract hostname from Host Info', msgLevel.ERROR)
        sys.exit(1)

if debug: 
    print(json.dumps(resp.out(), indent=4))

################################################################################
# 3) Add Cluster ASM
################################################################################

# Only one record per osm_cluster will be returned...
msg('looking for ASM Cluster *' + cluster, msgLevel.INFO)

targets = 'osm_cluster'
try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

for target in resp.out()['data']:
    m = re.match(r"host:(?P<host>\S+);", target['Host Info'])
    if m:
        host = m.group('host')
    else:
        msg('cannot extract hostname from Host Info', msgLevel.ERROR)
        sys.exit(1)

    m = re.search(r"ClusterName:(?P<ClusterName>[^;]+).*ServiceName:(?P<ServiceName>[^;]+)", target['Properties'])
    if m:
        ClusterName = m.group('ClusterName')
        ServiceName = m.group('ServiceName')
    else:
        msg('cannot extract ClusterName/ServiceName from Properties', msgLevel.ERROR)
        sys.exit(1)

    if ClusterName != cluster:
        continue

    # Got it! - back to where we started withe the cluster name

    instances = ';'.join([(lambda x:x+':osm_instance')(i) for i in osm_list])

    msg(ServiceName, level=msgLevel.INFO, tag='RAC Database')
    msg('add_target -name=' + target['Target Name'] +
        ' -type=osm_clustere -host=' + host +
        ' -monitor_mode=1 -properties="ServiceName:'+ServiceName+';ClusterName:'+ClusterName +'"' +
        ' -instances="'+instances+'"' +
        ' -credentials="UserName:' + dbsnmpuser + ';password=' + dbsnmppass + ';Role:sysdba"', msgLevel.USER, tag='EMCLI')

if debug: 
    print(json.dumps(resp.out(), indent=4))
