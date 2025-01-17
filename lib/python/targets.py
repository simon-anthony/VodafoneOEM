# emcliext
from emcli import *
from emcli.exception import VerbExecutionError

class NullTargets(Exception): pass
class EmptyTarget(Exception): pass
class InvalidTargetType(Exception): pass

class TargetsList:
    """Retrieve targets from OMS """

    def __init__(self, target_type):  # Initialize when created
        if not target_type:
            raise EmptyTarget

        if target_type == 'host':
            pass
        elif target_type == 'oracle_emd':
            pass
        elif target_type == 'oracle_database':
            pass
        else:
            raise InvalidTargetType

        self.targets_list = []

        try:
            targets = get_targets(targets='%:' + target_type)

        # except emcli.exception.VerbExecutionError, e:
        except VerbExecutionError, e:
            print e.error()
            exit(1)

        for target in targets.out()['data']:
            self.targets_list.append(target['Target Name'])


    """Is target in list?"""
    def inTargets(self, target):
        return target in self.targets_list

    """Is target NOT in list?"""
    def notInTargets(self, target):
        return target not in self.targets_list

    """Which target or list of targets is already in OEM?"""
    """Return a list"""
    def filterTargets(self, target):
        found_list = []

        if type(target) is str:
            if target in self.targets_list:
                found_list[0] = target
        elif type(target) is list:
            for item in target:
                if item in self.targets_list:
                    found_list.append(item)

        return found_list
                    
