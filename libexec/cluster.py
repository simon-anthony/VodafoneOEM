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

    log.debug(json.dumps(resp.out(), indent=4))

    return instances_list
    # access with
    # instances = ';'.join([(lambda x:x+':host')(i) for i in instances_list])
