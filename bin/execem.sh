#!/usr/bin/sh

PATH=/usr/bin:BINDIR export PATH
prog=`basename $0 .sh`

if [ "X$ORACLE_HOME" = "X" ]
then
	echo "$prog: ORACLE_HOME not set" >&2
	exit 1
fi
PATH=$PATH:$ORACLE_HOME/bin

if [ ! -d $ORACLE_HOME/bin/emcliext ]
then
	echo "$prog: directory $ORACLE_HOME/bin/emcliext does not exist" >&2
	exit 1
fi
# /opt/oracle/product/13c/mw/bin/emcliext/__pycache__

export PYTHONPATH=LIBDIR/python

prog=`basename $0 .sh`

usage() {
    cat >&2 <<-!
		usage: $prog [OPTION] -- <prog> [<args>]
		OPTION:
		  -l, --list                 List modules
		  -u, --username=NAME        Name of OMS user, default 'SYSMAN'
		  -v, --verbose              Verbose 
		  -?, --help                 Give this help list
	!
    exit 2
}

TEMP=`getopt -o lu:vh --long user,verbose,help \
     -n "$prog" -- "$@"`

[ $? != 0 ] && { usage; exit 1; }

# Note the quotes around `$TEMP': they are essential!
eval set -- "$TEMP"
typeset lflg= uflg= hflg= vflg= errflg=  
typeset username="SYSMAN"

while true
do
	case "$1" in
	-l|--list)
		lflg=y
		shift ;;
	-u|--username)
		uflg=y
		user=$2
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

if [ ! -r $PYTHONPATH/$file.py ] 
then
	echo "$prog: cannot find module '$file'" >&2
	exit 1
fi

emcli @$PYTHONPATH/$file.py $*
