import sys
import argparse
import ConfigParser
from utils import getcreds,keyvalues
import json
import re
import logging
import logging.config
from logging_ext import ColoredFormatter
from cluster import get_cluster,get_cluster_nodes_from_scan,get_osm_instances_on_hosts,get_osm_cluster


parser = argparse.ArgumentParser(
    prog='vf_promote_osm_cluster',
    description='Promote an ASM cluster after discovery',
    epilog='The .ini files found in @PKGDATADIR@ contain values for NODE (node.ini), REGION (region.ini)')

# Logging
parser.add_argument('-L', '--logfile', type=argparse.FileType('a'), default='/dev/null',
    metavar='PATH', help='write logging to a file')
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
logging.config.fileConfig('@PKGDATADIR@/logging.conf', defaults={'logfilename': args.logfile.name})
log = logging.getLogger(parser.prog) # create top level logger

numeric_level = getattr(logging, args.loglevel.upper(), None) # console log level
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)
log.setLevel(numeric_level)

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


################################################################################

# 1911671.1 How to add Cluster ASM Target
# 1908635.1 How to Discover the Cluster and Cluster Database (RAC) Target

################################################################################
# 1. Add the Cluster Target
################################################################################
log.info('retrieving cluster information')

# Retrieve information about the cluster, note that only *one* node will be
# present in the 'Host Info' (the last one to be discovered)
cluster_record = get_cluster(args.cluster)

# Retrieve the full list of host members from the SCAN listeners
instances_list = get_cluster_nodes_from_scan(cluster_record['Target Name'], cluster_record['scanName'])

instances = ';'.join([(lambda x:x+':host')(i) for i in instances_list])

log.notice('add_target -name=' + cluster_record['Target Name'] +
    ' -type=cluster -host=' + cluster_record['host'] +
    ' -monitor_mode=1' +
    ' -properties=OracleHome:' + cluster_record['OracleHome'] + ';scanName:' + cluster_record['scanName'] + ';scanPort:' + cluster_record['scanPort'] +
    ' -instances=' + instances)


################################################################################
# 2) Add the ASM Instance Targets
################################################################################
log.info('ASM instances on ' + ' '.join(instances_list))

osm_records_list = get_osm_instances_on_hosts(instances_list)

for osm in osm_records_list:
    log.notice('add_target -name=' + osm['Target Name'] +
        ' -type=osm_instance' +
        ' -host=' + osm['host'] +
        ' -credentials="UserName:' + asmsnmpuser + ';password=' + asmsnmppass + ';Role:sysdba"' +
        ' -properties="SID:' + osm['SID'] + ';Port:' + osm['Port'] + ';OracleHome:' + osm['OracleHome'] + ';MachineName:' + osm['MachineName']+'"')

################################################################################
# 3) Add Cluster ASM
################################################################################
log.info('ASM cluster ' + cluster_record['Target Name']) # only one record per osm_cluster will be returned...

osm_record = get_osm_cluster(cluster_record['Target Name'])

instances = ';'.join([(lambda x:x+':osm_instance')(i) for i in instances_list])

log.notice('add_target -name=' + osm_record['Target Name'] +
    ' -type=osm_cluster -host=' + osm_record['host'] +
    ' -monitor_mode=1 ' +
    ' -properties="ServiceName:' + osm_record['ServiceName'] + ';ClusterName:' + osm_record['ClusterName'] + '"' +
    ' -instances="' + instances + '"' +
    ' -credentials="UserName:' + asmsnmpuser + ';password=' + asmsnmppass + ';Role:sysdba"')

