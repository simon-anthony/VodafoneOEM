#!/usr/bin/sh

PATH=/usr/bin:BINDIR export PATH
prog=`basename $0 .sh`

export PYTHONPATH=LIBEXECDIR/PACKAGE
# EMCLI_PYTHONPATH is for modules (i.e. libraries) but does not appear to work
export EMCLI_PYTHONPATH=LIBDIR/pythonPYTHON_VERSION/site-packages/PACKAGE:$EMCLI_PYTHONPATH

prog=`basename $0 .sh`

usage() {
    cat >&2 <<-!
		usage: $prog [OPTION] -- <module> [-h|--help] [<args>]
		OPTION:
		  -l, --list                 List modules
		  -s, --sid=NAME             Set ORACLE_HOME for NAME
		  -v, --verbose              Verbose 
		  -?, --help                 Give this help list
	!
    exit 2
}

TEMP=`getopt -o ls:vh --long sid,verbose,help \
     -n "$prog" -- "$@"`

[ $? != 0 ] && { usage; exit 1; }

# Note the quotes around `$TEMP': they are essential!
eval set -- "$TEMP"
typeset lflg= sflg= hflg= vflg= errflg=  

while true
do
	case "$1" in
	-l|--list)
		lflg=y
		shift ;;
	-s|--sid)
		sflg=y
		sid=$2
		shift 2 ;;
    -v|--verbose)
        vflg=y
        shift ;;
    -h|--help)
        hflg=y
        shift ;;
    #-h|--help)
    #    errflg=y
    #    shift; break ;;
    --) shift; break ;;
    *)  errflg=y; break ;;
    esac
done

if [ $lflg ]
then
	if [ $vflg ]
	then
		for i in `ls $PYTHONPATH/*.py`
		do
			emcli @$i -h | sed -n '1,/^$/ p'
		done
	else 
		ls $PYTHONPATH/*.py | xargs basename -s .py
	fi
	exit
fi

[ $# -eq 0 ] && errflg=y

[ $errflg ] && usage

file=`basename $1 .py`
shift

[ -r SYSCONFDIR/profile.d/setoraenv.sh ] && . SYSCONFDIR/profile.d/setoraenv.sh

if [ $sflg ] # set ORACLE_HOME
then
	setoraenv -s $sid || exit
else # pick up from env
	if [ "X$ORACLE_HOME" = "X" ]
	then
		echo "$prog: ORACLE_HOME not set" >&2
		exit 1
	fi
	PATH=$PATH:$ORACLE_HOME/bin
fi

if [ ! -d $ORACLE_HOME/bin/emcliext ]
then
	echo "$prog: directory $ORACLE_HOME/bin/emcliext does not exist" >&2
	exit 1
	# $ORACLE_HOME/bin/emcliext/__pycache__ for compiled stuff
fi
EMCLI_PYTHONPATH=$ORACLE_HOME/bin/emcliext:$EMCLI_PYTHONPATH

if [ ! -r $PYTHONPATH/$file.py ] 
then
	echo "$prog: cannot find module '$file'" >&2
	exit 1
fi

emcli @$PYTHONPATH/$file.py $*
