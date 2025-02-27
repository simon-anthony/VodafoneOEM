import sys
import argparse
import ConfigParser
from utils import getcreds
import json
import re
import logging
from logging_ext import ColoredFormatter
from cluster import get_cluster_nodes_from_scan,get_databases_on_hosts


parser = argparse.ArgumentParser(
    prog='promote_cluster',
    description='Promote a cluster after discovery',
    epilog='The .ini files found in @PKGDATADIR@ contain values for NODE (node.ini), REGION (region.ini)')

# Logging
log = logging.getLogger(parser.prog) # create top level logger

parser.add_argument('-L', '--logfile', type=argparse.FileType('a'), metavar='PATH', help='write logging to a file')
parser.add_argument('-V', '--loglevel', default='NOTICE', metavar='LEVEL',
    choices=['DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'CRITICAL'], help='console log level: %(choices)s')

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
parser.add_argument('-s', '--dbsnmpuser', help='DB SNMP user, overides that found in @PKGDATADIR@/node.ini')
parser.add_argument('-a', '--asmsnmpuser', help='ASM SNMP user, overides that found in @PKGDATADIR@/node.ini')

# only one positional argument - the cluster
parser.add_argument('cluster', metavar='CLUSTER', help='name of cluster')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)

if args.region:
    oms = config_region.get(args.region, 'url')
else:
    oms = args.oms

# Set up logging
numeric_level = getattr(logging, args.loglevel.upper(), None) # console log level
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)

ch = logging.StreamHandler() # add console handler 
ch.setLevel(numeric_level)
ch.setFormatter(ColoredFormatter("%(name)s[%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"))
log.addHandler(ch)

if args.logfile:
    fh = logging.FileHandler(args.logfile.name) # add file handler
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log.addHandler(fh)

log.setLevel(logging.NOTICE) # fallback log level (default WARNING)

log.notice('connecting to ' + oms)

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
    log.error('unable to determine username to use')
    sys.exit(1)

log.notice('username = ' + username)

login(username=username, password=creds['password'])

# retrieve dbsnmp password
if args.dbsnmpuser:
    dbsnmpuser = args.dbsnmpuser
else:
    dbsnmpuser = config_node.get(args.node, 'dbsnmpuser')

if not dbsnmpuser:
    log.error('unable to determine username for DB snmp')
    sys.exit(1)

dbsnmpcreds = getcreds(dbsnmpuser)
dbsnmppass = dbsnmpcreds['password']

log.notice('DB SNMP username = ' + dbsnmpuser)

# retrieve asmsnmp password
if args.asmsnmpuser:
    asmsnmpuser = args.asmsnmpuser
else:
    asmsnmpuser = config_node.get(args.node, 'asmsnmpuser')

if not asmsnmpuser:
    log.error('unable to determine username for DB snmp')
    sys.exit(1)

asmsnmpcreds = getcreds(asmsnmpuser)
asmsnmppass = asmsnmpcreds['password']

log.notice('ASM SNMP username = ' + asmsnmpuser)

# Retrieve information about the cluster, note that only *one* node will be
# present in the 'Host Info' (the last one to be discovered)
targets = args.cluster + ':' + 'cluster'

try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    log.error(e.error())
    exit(1)

if len(resp.out()['data']) == 0:
    log.error('no such cluster ' + args.cluster)
    sys.exit(1)

# 1911671.1 How to add Cluster ASM Target
# 1908635.1 How to Discover the Cluster and Cluster Database (RAC) Target

################################################################################
# 1. Add the Cluster Target
################################################################################

####
# i. Add the cluster (cluster) target
####

cluster = resp.out()['data'][0]['Target Name']  # there will be only one record
log.info('cluster: ' + cluster)

m = re.match(r"host:(?P<host>\S+);", resp.out()['data'][0]['Host Info'])
if m:
    host = m.group('host')
else:
    log.error('cannot extract hostname from Host Info')
    sys.exit(1)

m = re.search(r"OracleHome:(?P<OracleHome>[^;]+).*scanName:(?P<scanName>[^;]+).*scanPort:(?P<scanPort>\d+)", resp.out()['data'][0]['Properties'])
if m:
    OracleHome = m.group('OracleHome')
    scanName = m.group('scanName')
    scanPort = m.group('scanPort')
else:
    log.error('cannot extract OracleHome/scanName/scanPort from Properties')
    sys.exit(1)

log.debug(json.dumps(resp.out(), indent=4))

# Retrieve the full list of host members from the SCAN listeners
instances_list = get_cluster_nodes_from_scan(cluster, scanName)

instances = ';'.join([(lambda x:x+':host')(i) for i in instances_list])

log.info('instances: ' + instances)

log.notice('add_target -name=' + cluster +
    ' -type=cluster -host=' + host + 
    ' -monitor_mode=1' +
    ' -properties=OracleHome:' + OracleHome + ';scanName:' + scanName + ';scanPort:' + scanPort + 
    ' -instances=' + instances)


####
#  ii. Add the database instance (oracle_database) targets
# iii. Add the remainig nodes
####
# There may be multiples DBs on instance for cluster
databases_list = get_databases_on_hosts(instances_list)

for db in databases_list:
    log.info('ServiceName: ' + db['ServiceName'])

    log.notice('add_target -name='+ db['target'] +
        ' -type=oracle_database' +
        ' -host=' + db['host'] +
        ' -credentials="UserName:' + dbsnmpuser + ';password=' + dbsnmppass + ';Role:Normal"' +
        ' -properties="SID:' + db['SID'] + ';Port:' + db['Port'] + ';OracleHome:' + db['OracleHome'] + ';MachineName:' + db['MachineName'] + '"')

####
#  iv. Add the Cluster database (rac_database) target
####
# Find the rac_database with ServiceName the same as the oracle_databases
# Only one record per rac_database will be returned...

log.info('looking for rac_database ' + ServiceName)

targets = 'rac_database'
try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    log.error(e.error())
    exit(1)

for target in resp.out()['data']:   # multiple records
    if target['Target Name'] != ServiceName:  
        continue
    # got it!

    m = re.match(r"host:(?P<host>\S+);", target['Host Info'])
    if m:
        host = m.group('host')
    else:
        log.error('cannot extract hostname from Host Info')
        sys.exit(1)

    m = re.search(r"ClusterName:(?P<ClusterName>[^;]+).*ServiceName:(?P<ServiceName>[^;]+)", target['Properties'])
    if m:
        ClusterName = m.group('ClusterName')
        ServiceName = m.group('ServiceName')
    else:
        log.error('cannot extract ClusterName/ServiceName from Properties')
        sys.exit(1)

    instances = ';'.join([(lambda x:x+':oracle_database')(i) for i in dbs_list])

    log.info('RAC Database ' + ServiceName)
    log.notice('add_target -name=' + target['Target Name'] +
        ' -type=rac_database' +
        ' -host=' + host +
        ' -monitor_mode=1' +
        ' -properties="ServiceName:' + ServiceName + ';ClusterName:' + ClusterName + '"' +
        ' -instances="' + instances + '"')

log.debug(json.dumps(resp.out(), indent=4))

################################################################################
# 2) Add the ASM Instance Targets
################################################################################

log.info('looking for ASM instances on ' + ' '.join(instances_list))

targets = 'osm_instance'
try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    log.error(e.error())
    exit(1)

osm_list = [] # needed for the targets to add to osm_cluster
for target in resp.out()['data']:   # multiple records
    m = re.match(r"host:(?P<host>\S+);", target['Host Info'])
    if m:
        host = m.group('host')
        log.info('ASM Instance ' + host)
        if host in instances_list: # check host is one of our instances, otherwise ignore
            osm_list.append(target['Target Name']) 
            m = re.search(r"MachineName:(?P<MachineName>[^;]+).*OracleHome:(?P<OracleHome>[^;]+).*Port:(?P<Port>[^;]+).*SID:(?P<SID>[^;]+)", target['Properties'])
            if m:
                MachineName = m.group('MachineName')
                OracleHome = m.group('OracleHome')
                Port = m.group('Port')
                SID = m.group('SID')

                log.notice('add_target -name=' + target['Target Name'] +
                ' -type=osm_instance' +
                ' -host=' + host +
                ' -credentials="UserName:' + dbsnmpuser + ';password=' + dbsnmppass + ';Role:sysdba"' +
                ' -properties="SID:' + SID + ';Port:' + Port + ';OracleHome:' + OracleHome + ';MachineName:' + MachineName+'"')
            else:
                log.error('cannot extract MachineName/OracleHome/Port/SID from Properties')
                sys.exit(1)
    else:
        log.error('cannot extract hostname from Host Info')
        sys.exit(1)

log.debug(json.dumps(resp.out(), indent=4))

################################################################################
# 3) Add Cluster ASM
################################################################################

# Only one record per osm_cluster will be returned...
log.info('looking for ASM Cluster ' + cluster)

targets = 'osm_cluster'
try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    log.error(e.error())
    exit(1)

for target in resp.out()['data']:
    m = re.match(r"host:(?P<host>\S+);", target['Host Info'])
    if m:
        host = m.group('host')
    else:
        log.error('cannot extract hostname from Host Info')
        sys.exit(1)

    m = re.search(r"ClusterName:(?P<ClusterName>[^;]+).*ServiceName:(?P<ServiceName>[^;]+)", target['Properties'])
    if m:
        ClusterName = m.group('ClusterName')
        ServiceName = m.group('ServiceName')
    else:
        log.error('cannot extract ClusterName/ServiceName from Properties')
        sys.exit(1)

    if ClusterName != cluster:
        continue

    # Got it! - back to where we started withe the cluster name

    instances = ';'.join([(lambda x:x+':osm_instance')(i) for i in osm_list])

    log.info('ASM Cluster ' + ServiceName)
    log.notice('add_target -name=' + target['Target Name'] +
        ' -type=osm_cluster -host=' + host +
        ' -monitor_mode=1 ' +
        ' -properties="ServiceName:' + ServiceName + ';ClusterName:' + ClusterName + '"' +
        ' -instances="' + instances + '"' +
        ' -credentials="UserName:' + asmsnmpuser + ';password=' + asmsnmppass + ';Role:sysdba"')

log.debug(json.dumps(resp.out(), indent=4))
