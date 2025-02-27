# emcliext

import argparse

class CustomExtend(argparse.Action):
    """Jython (Python 2.7) does not have action='extend' (used with nargs='+')"""
    """so we cannot do:"""
    """    -p 'prop1' 'prop2' -p 'prop3' and get args.property=['prop1', 'prop2', 'prop3']"""
    """This custom argparse action allows that and to optionally clear the"""
    """default value from being included by setting the custom parameter defaultextended=False"""
    """Note that nargs='+' is the default"""
    """Example use: """
    """   parser.add_argument('-p', '--property', nargs='+', action=CustomExtend, metavar='PROPERTY', """
    """     default=['Lifecycle Status', 'Cost Center', 'Department'], """
    """     defaultextended=False, """
    """     help='list of properties, default is %(default)s')"""
    def __init__(self,
            option_strings,
            dest=None,
            nargs='+',
            default=None,
            required=False,
            type=None,
            metavar=None,
            help=None,
            defaultextended=True):
        self.default = default
        self.defaultextended = defaultextended
        super(CustomExtend, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=nargs,
            default=default,
            required=required,
            metavar=metavar,
            type=type,
            help=help)
    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest) or []
        if not self.defaultextended:
            if items == self.default:
                items = []
        items.extend(values)
        setattr(namespace, self.dest, items)

#
