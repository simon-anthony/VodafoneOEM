# emcliext
import logging
import re
import sys
import json
from emcli import *
from emcli.exception import VerbExecutionError
from logging_ext import ColoredFormatter
import os.path
import inspect


def getprop(name, string):
    m = re.search(r"{name}:(?P<value>[^;]+).*".format(name=name), string)
    if m:
        return m.group('value')
    log.error('Cannot find ' + name + ' in ' + string)
    return None


def get_cluster(cluster):
    """return dict with information about the clusetr database with the given cluster name"""
    """there is only one record in the discovery catalog as this is the"""
    """last record added"""

    log = logging.getLogger(os.path.splitext(os.path.basename(inspect.stack()[1][1]))[0] +'.'+
        os.path.splitext(os.path.basename(__file__))[0].replace('$py','') +'.'+
        sys._getframe().f_code.co_name)

    log.debug("cluster name is " + cluster)

    targets = cluster + ':cluster'
    try:
        resp = get_targets(targets = targets, unmanaged = True, properties = True)

    except emcli.exception.VerbExecutionError, e:
        log.error(e.error())
        exit(1)

    if len(resp.out()['data']) == 0:
        log.error('no such cluster ' + args.cluster)
        sys.exit(1)

    log.debug(json.dumps(resp.out(), indent=4))

    obj = resp.out()['data'][0]
    host = getprop('host', obj['Host Info'])

    cluster_dict = {
        'Target Name': obj['Target Name'],
        'OracleHome': getprop('OracleHome', obj['Properties']),
        'eonsPort': getprop('eonsPort', obj['Properties']),
        'scanName': getprop('scanName', obj['Properties']),
        'scanPort': getprop('scanPort', obj['Properties']),
        'host': host }

    return cluster_dict


def get_cluster_nodes_from_scan(cluster, scanName, unmanaged=True):
    """Retrieve the full list of host members from the SCAN listeners"""

    log = logging.getLogger(os.path.splitext(os.path.basename(inspect.stack()[1][1]))[0] +'.'+
        os.path.splitext(os.path.basename(__file__))[0].replace('$py','') +'.'+
        sys._getframe().f_code.co_name)

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

    for obj in resp.out()['data']:   # multiple records
        instance = getprop('host', obj['Host Info'])
        Machine = getprop('Machine', obj['Properties'])
        if Machine == scanName: # check Machine matches scanName, otherwise ignore
            if instance not in instances_list: # avoid duplication
                instances_list.append(instance) 

    log.info(instances_list)

    # access with
    # instances = ';'.join([(lambda x:x+':host')(i) for i in instances_list])
    return instances_list


def get_databases_on_hosts(instances_list):
    """Return list of dictionary entries of database targets in instances in list"""
    """[{ 'Target Name':'', 'host':'', 'SID':'', 'MachineName':'', 'OracleHome:'',, 'Port':'', 'ServiceName':''},"""
    """ { 'Target Name':'', 'host':'', 'SID':'', 'MachineName':'', 'OracleHome:'',, 'Port':'', 'ServiceName':''}, ...]"""

    log = logging.getLogger(os.path.splitext(os.path.basename(inspect.stack()[1][1]))[0] +'.'+
        os.path.splitext(os.path.basename(__file__))[0].replace('$py','') +'.'+
        sys._getframe().f_code.co_name)

    targets = 'oracle_database'

    try:
        resp = get_targets(targets = targets, unmanaged = True, properties = True)

    except emcli.exception.VerbExecutionError, e:
        log.error(e.error())
        exit(1)

    log.debug(json.dumps(resp.out(), indent=4))

    dbs_list = [] # needed for the targets to add to rac_database

    for obj in resp.out()['data']:   # multiple records
        host = getprop('host', obj['Host Info'])

        if host in instances_list: # check host is one of our instances, otherwise ignore
            log.info('oracle_database ' + host)

            dbs_list.append({
                'Target Name':obj['Target Name'],
                'host':host,
                'SID':getprop('SID', obj['Properties']),
                'MachineName':getprop('MachineName', obj['Properties']),
                'OracleHome':getprop('OracleHome', obj['Properties']),
                'Port':getprop('Port', obj['Properties']),
                'ServiceName':getprop('ServiceName', obj['Properties'])})
    return dbs_list



def get_rac_database(ServiceName):
    """return dict with information about the RAC database with the given ServiceName"""
    """there is only one record in the discovery catalog as this is the"""
    """last record added"""

    log = logging.getLogger(os.path.splitext(os.path.basename(inspect.stack()[1][1]))[0] +'.'+
        os.path.splitext(os.path.basename(__file__))[0].replace('$py','') +'.'+
        sys._getframe().f_code.co_name)

    targets = 'rac_database'
    try:
        resp = get_targets(targets = targets, unmanaged = True, properties = True)

    except emcli.exception.VerbExecutionError, e:
        log.error(e.error())
        exit(1)

    log.debug(json.dumps(resp.out(), indent=4))

    #    cluster_dict = { key: None for key in ['Target Name', 'ClusterName', 'ServiceName', 'host']}

    for obj in resp.out()['data']:   # multiple records
        if obj['Target Name'] != ServiceName:  
            continue
        # got it!

        host = getprop('host', obj['Host Info'])

        cluster_dict = {
            'Target Name': obj['Target Name'],
            'ClusterName': getprop('ClusterName', obj['Properties']),
            'ServiceName': getprop('ServiceName', obj['Properties']),
            'host': host }

        return cluster_dict


def get_osm_instances_on_hosts(instances_list):
    """Return list of dictionary entries of osm targets in instances in list"""
    """[{ 'Target Name':'', 'host':'', 'SID':'', 'MachineName':'', 'OracleHome':'', 'Port':''},"""
    """ { 'Target Name':'', 'host':'', 'SID':'', 'MachineName':'', 'OracleHome':'', 'Port':''}, ...]"""

    log = logging.getLogger(os.path.splitext(os.path.basename(inspect.stack()[1][1]))[0] +'.'+
        os.path.splitext(os.path.basename(__file__))[0].replace('$py','') +'.'+
        sys._getframe().f_code.co_name)

    targets = 'osm_instance'
    try:
        resp = get_targets(targets = targets, unmanaged = True, properties = True)

    except emcli.exception.VerbExecutionError, e:
        log.error(e.error())
        exit(1)

    log.debug(json.dumps(resp.out(), indent=4))

    osm_list = [] # needed for the targets to add to osm_cluster

    for obj in resp.out()['data']:   # multiple records
        host = getprop('host', obj['Host Info'])
        log.info('ASM Instance ' + host)
        if host in instances_list: # check host is one of our instances, otherwise ignore
      
            osm_list.append({
                'Target Name':obj['Target Name'],
                'host':host,
                'SID':getprop('SID', obj['Properties']),
                'MachineName':getprop('MachineName', obj['Properties']),
                'OracleHome':getprop('OracleHome', obj['Properties']),
                'Port':getprop('Port', obj['Properties'])})

    return osm_list


def get_osm_cluster(cluster):
    """return dict with information about the cluster given cluster name"""
    """there is only one record in the discovery catalog as this is the"""
    """last record added"""

    log = logging.getLogger(os.path.splitext(os.path.basename(inspect.stack()[1][1]))[0] +'.'+
        os.path.splitext(os.path.basename(__file__))[0].replace('$py','') +'.'+
        sys._getframe().f_code.co_name)

    targets = 'osm_cluster'

    try:
        resp = get_targets(targets = targets, unmanaged = True, properties = True)

    except emcli.exception.VerbExecutionError, e:
        log.error(e.error())
        exit(1)

    log.debug(json.dumps(resp.out(), indent=4))

    for obj in resp.out()['data']:
        host = getprop('host', obj['Host Info'])

        ClusterName = getprop('ClusterName', obj['Properties'])
        ServiceName = getprop('ServiceName', obj['Properties'])

        if ClusterName != cluster:
            continue

        # Got it! 

        log.info('ASM Cluster ' + ServiceName)
        osm_cluster_dict = {
            'Target Name': obj['Target Name'],
            'ClusterName': ClusterName,
            'ServiceName': ServiceName,
            'host': host }

        return osm_cluster_dict





################################################################################
#
# Example of using key value split rather than regex
#
#    host = getprop('host', obj['Host Info'])
#
#    if host in instances_list: # check host is one of our instances, otherwise ignore
#        log.info('oracle_database ' + host)
#
#        for key, value in {k: v for k, v in (item.split(":") for item in obj["Properties"].split(";"))}.items():
#            log.debug(key + ' = ' + value)
#            if value.isdigit():
#                exec(key + ' = ' + 'int(' +  value + ')')
#            else:
#                exec(key + ' = ' + '"' + value + '"')
#        dbs_list.append({
#            'target':object['Target Name'],
#            'host':host,
#            'SID':SID,
#            'MachineName':MachineName,
#            'OracleHome':OracleHome,
#            'Port':Port,
#            'ServiceName':ServiceName})
