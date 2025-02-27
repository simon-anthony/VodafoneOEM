# emcliext

include argparse

class CustomExtend(argparse.Action):
    """Jython (Python 2.7) does not have action='extend' (used with nargs='+')"""
    """so we cannot do:"""
    """-p 'prop1' 'prop2' -p 'prop3' and get args.property=['prop1', 'prop2', 'prop3']"""
    """This custom argparse action allows that and to optionally clear the"""
    """default"""
    def __init__(self,
            option_strings,
            dest=None,
            nargs=0,
            default=None,
            required=False,
            type=None,
            metavar=None,
            help=None):
        self.default = default
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
        if items == self.default:
            items = []
        items.extend(values)
        setattr(namespace, self.dest, items)

#parser.add_argument('-p', '--properties', '--property', nargs='+', action=r_extend, metavar='PROPERTY',
#    default=['Lifecycle Status', 'Cost Center', 'Department'],
#   help='list of properties, default is %(default)s')
