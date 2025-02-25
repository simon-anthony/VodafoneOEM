import sys
import argparse
import ConfigParser
from utils import getcreds
from utils import msg, msgLevel, msgColor
import json
import re
import logging
from logging_ext import ColoredFormatter


parser = argparse.ArgumentParser(
    prog='promote_cluster',
    description='Promote a cluster after discovery',
    epilog='The .ini files found in @PKGDATADIR@ contain values for NODE (node.ini), REGION (region.ini)')

# Logging
log = logging.getLogger(parser.prog) # create top level logger

parser.add_argument('-L', '--logfile', type=argparse.FileType('a'), metavar='PATH', help='write logging to a file')
parser.add_argument('-V', '--loglevel', default='INFO', metavar='LEVEL',
    choices=['DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'CRITICAL'], help='console log level')

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

log.setLevel(logging.DEBUG) # fallback log (default WARNING)

log.info('connecting to ' + oms)

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

log.info('username = ' + username)

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

log.info('DB SNMP username = ' + dbsnmpuser)

# Retrieve information about the cluster, note that only *one* node will be
# present in the 'Host Info' (the last one to be discovered)
targets = args.cluster + ':' + 'cluster'

try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    print e.error()
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
targets = 'LISTENER_SCAN%_' + cluster + ':oracle_listener'
try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    log.error(e.error())
    exit(1)

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
            log.error('cannot extract MachineName from Properties')
    else:
        log.error('cannot extract hostname from Host Info')
        sys.exit(1)

instances = ';'.join([(lambda x:x+':host')(i) for i in instances_list])

log.info('instances: ' + instances)

log.notice('add_target -name='+ cluster + ' -type=cluster -host=' + host + ' -monitor_mode=1 -properties=OracleHome:' + OracleHome + ';scanName:' + scanName + ';scanPort:' + scanPort + ' -instances=' + instances)

log.debug(json.dumps(resp.out(), indent=4))

####
#  ii. Add the database instance (oracle_database) targets
# iii. Add the remainig nodes
####
# Assume only DBs on instance are for cluster

targets = 'oracle_database'
try:
    resp = get_targets(targets = targets, unmanaged = True, properties = True)

except emcli.exception.VerbExecutionError, e:
    log.error(e.error())
    exit(1)

dbs_list = [] # needed for the targets to add to rac_database
for target in resp.out()['data']:   # multiple records
    m = re.match(r"host:(?P<host>\S+);", target['Host Info'])
    if m:
        host = m.group('host')
        log.info('oracle_database ' + host)
        if host in instances_list: # check host is one of our instances, otherwise ignore
            dbs_list.append(target['Target Name']) 
            m = re.search(r"SID:(?P<SID>[^;]+).*MachineName:(?P<MachineName>[^;]+).*OracleHome:(?P<OracleHome>[^;]+).*Port:(?P<Port>[^;]+).*ServiceName:(?P<ServiceName>[^;]+)", target['Properties'])
            if m:
                SID = m.group('SID')
                MachineName = m.group('MachineName')
                OracleHome = m.group('OracleHome')
                Port = m.group('Port')
                ServiceName = m.group('ServiceName')

                log.notice('add_target -name='+ target['Target Name'] +
                ' -type=oracle_database' +
                ' -host=' + host +
                ' -credentials="UserName:' + dbsnmpuser + ';password=' + dbsnmppass + ';Role:Normal"' +
                ' -properties="SID:'+SID+';Port:'+Port+';OracleHome:'+OracleHome+';MachineName:'+MachineName+'"')
            else:
                log.error('cannot extract SID/MachineName/OracleHome/Port/ServiceName from Properties')
                sys.exit(1)
    else:
        log.error('cannot extract hostname from Host Info')
        sys.exit(1)

log.debug(json.dumps(resp.out(), indent=4))

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
        ' -type=rac_database -host=' + host +
        ' -monitor_mode=1 -properties="ServiceName:'+ServiceName+';ClusterName:'+ClusterName+'" -instances="'+instances+'"')

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

                log.notice('add_target -name='+ target['Target Name'] +
                ' -type=osm_instance' +
                ' -host=' + host +
                ' -credentials="UserName:' + dbsnmpuser + ';password=' + dbsnmppass + ';Role:sysdba"' +
                ' -properties="SID:'+SID+';Port:'+Port+';OracleHome:'+OracleHome+';MachineName:'+MachineName+'"')
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
    print e.error()
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

    log.info('RAC Database '+ServiceName)
    log.notice('add_target -name=' + target['Target Name'] +
        ' -type=osm_cluster -host=' + host +
        ' -monitor_mode=1 -properties="ServiceName:'+ServiceName+';ClusterName:'+ClusterName +'"' +
        ' -instances="'+instances+'"' +
        ' -credentials="UserName:' + dbsnmpuser + ';password=' + dbsnmppass + ';Role:sysdba"')

log.debug(json.dumps(resp.out(), indent=4))
