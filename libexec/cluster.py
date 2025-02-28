# emcliext
import logging
import re
import sys
import json
from emcli import *
from emcli.exception import VerbExecutionError
from logging_ext import ColoredFormatter

#log = logging.getLogger('promote_cluster.' + __name__)


def get_cluster_nodes_from_scan(cluster, scanName, unmanaged=True):
    """Retrieve the full list of host members from the SCAN listeners"""

    log = logging.getLogger('promote_cluster.' + sys._getframe().f_code.co_name)

    log.debug("SCAN name is " + scanName)

    targets = 'LISTENER_SCAN%_' + cluster + ':oracle_listener'

    if unmanaged:
        properties = True
    else:
        properties = False

    try:
        resp = get_targets(targets = targets, unmanaged = unmanaged, properties = properties)

    except emcli.exception.VerbExecutionError, e:
        log.error(e.error())
        exit(1)

    log.debug(json.dumps(resp.out(), indent=4))

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

    log.info(instances_list)

    # access with
    # instances = ';'.join([(lambda x:x+':host')(i) for i in instances_list])
    return instances_list


def get_databases_on_hosts(instances_list):
    """Return list of dictionary entries of database targets in instances in list"""
    """[{ 'target':'target_host_SID1', 'host':'vdf1.example.com', 'SID':'SID1', 'MachineName':'vdf1.example.com',...},"""
    """ { 'target':'target_host_SID2', 'host':'vdf2.example.com', 'SID':'SID2', 'MachineName':'vdf2.example.com',...}, ...]"""

    log = logging.getLogger('promote_cluster.' + sys._getframe().f_code.co_name)

    targets = 'oracle_database'

    try:
        resp = get_targets(targets = targets, unmanaged = True, properties = True)

    except emcli.exception.VerbExecutionError, e:
        log.error(e.error())
        exit(1)

    dbs_list = [] # needed for the targets to add to rac_database

    for obj in resp.out()['data']:   # multiple records
        m = re.match(r"host:(?P<host>\S+);", obj['Host Info'])
        if m:
            host = m.group('host')

            if host in instances_list: # check host is one of our instances, otherwise ignore
                log.info('oracle_database ' + host)

                m = re.search(r"SID:(?P<SID>[^;]+).*MachineName:(?P<MachineName>[^;]+).*OracleHome:(?P<OracleHome>[^;]+).*Port:(?P<Port>[^;]+).*ServiceName:(?P<ServiceName>[^;]+)", obj['Properties'])
                if m:
                    dbs_list.append({
                        'target':obj['Target Name'],
                        'host':host,
                        'SID':m.group('SID'),
                        'MachineName':m.group('MachineName'),
                        'OracleHome':m.group('OracleHome'),
                        'Port':m.group('Port'),
                        'ServiceName':m.group('ServiceName')})
                else:
                    log.error('cannot extract SID/MachineName/OracleHome/Port/ServiceName from Properties')
                    sys.exit(1)
        else:
            log.error('cannot extract hostname from Host Info')
            sys.exit(1)
    return dbs_list


def get_databases_on_hosts2(instances_list):
    """Return list of dictionary entries of database targets in instances in list"""
    """This version uses key value split rather than regex"""

    log = logging.getLogger('promote_cluster.' + sys._getframe().f_code.co_name)

    targets = 'oracle_database'

    try:
        resp = get_targets(targets = targets, unmanaged = True, properties = True)

    except emcli.exception.VerbExecutionError, e:
        log.error(e.error())
        exit(1)

    dbs_list = [] # needed for the targets to add to rac_database

    for obj in resp.out()['data']:   # multiple records
        m = re.match(r"host:(?P<host>\S+);", obj['Host Info'])
        if m:
            host = m.group('host')

            if host in instances_list: # check host is one of our instances, otherwise ignore
                log.info('oracle_database ' + host)

                for key, value in {k: v for k, v in (item.split(":") for item in obj["Properties"].split(";"))}.items():
                    log.debug(key + ' = ' + value)
                    if value.isdigit():
                        exec(key + ' = ' + 'int(' +  value + ')')
                    else:
                        exec(key + ' = ' + '"' + value + '"')
                dbs_list.append({
                    'target':object['Target Name'],
                    'host':host,
                    'SID':SID,
                    'MachineName':MachineName,
                    'OracleHome':OracleHome,
                    'Port':Port,
                    'ServiceName':ServiceName})
        else:
            log.error('cannot extract hostname from Host Info')
            sys.exit(1)
    return dbs_list

