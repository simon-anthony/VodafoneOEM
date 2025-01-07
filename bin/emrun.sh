#!/usr/bin/sh

PATH=/usr/bin:BINDIR export PATH
prog=`basename $0 .sh`
export PROG=$prog

export MODULEDIR=LIBEXECDIR/PACKAGE
export PYTHONPATH=LIBDIR/pythonPYTHON_VERSION
# EMCLI_PYTHONPATH is for modules (i.e. libraries) but does not appear to
# work...
export EMCLI_PYTHONPATH=LIBDIR/pythonPYTHON_VERSION

prog=`basename $0 .sh`

usage() {
    cat >&2 <<-!
		usage: $prog [OPTION] -- <module> [-h|--help] [<args>]
		OPTION:
		  -l, --list                 List modules
		  -s, --sid=NAME             Set ORACLE_HOME (OMS/Agent) for NAME
		  -k, --keyring              Create keyring
		  -f, --force                Force overwite of existing keyring
		  -i, --initialise           Initialise for use
		  -v, --verbose              Verbose 
		  -?, --help                 Give this help list
	!
    exit 2
}

TEMP=`getopt -o ls:kifvh --long list,sid,keyring,initialise,force,verbose,help \
     -n "$prog" -- "$@"`

[ $? != 0 ] && { usage; exit 1; }

# Note the quotes around `$TEMP': they are essential!
eval set -- "$TEMP"
typeset lflg= sflg= kflg= fflg= iflg= vflg= hflg= errflg=  

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
	-k|--keyring)
		kflg=y
		[ $iflg ] && errflg
		shift ;;
	-f|--force)
		fflg=y
		shift ;;
	-i|--initialise)
		iflg=y
		[ $kflg ] && errflg
		shift ;;
    -v|--verbose)
        vflg=y
        shift ;;
    -h|--help)
        hflg=y
        shift ;;
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

[ $# -eq 0 -a -z "$kflg" ] && errflg=y
[ "$fflg" -a -z "$kflg" ] && errflg=y	# -f requires -k

#[ $errflg ] && usage

# Check keyring and passwords

if [ $kflg ]
then
	[ $fflg ] && rm -rf $HOME/.local/share/keyrings
	[ -r $HOME/.local/share/keyrings/login.keyring ] && {
		echo "$prog: login keyring exists, re-run with -f to overwrite" >&2
		exit 1
	}
	if [ $DBUS_SESSION_BUS_ADDRESS ]
	then 
		exec BINDIR/unlock-keyring
	else
		exec dbus-run-session -- BINDIR/unlock-keyring
	fi
fi

if ! [ -r $HOME/.local/share/keyrings/login.keyring ]
then
	echo "$prog: login keyring does not exist, re-run with -k" >&2
	exit 1
fi

keyfile=$HOME/.config/emcli/username.key 
mkdir -p `dirname $keyfile`

if [ ! -r $keyfile ]	# Create a key
then
	if [ $iflg ]
	then
		echo "$prog: creating key" >&2
		key=`python <<-!
			import secrets

			secret = secrets.token_hex(nbytes=16)
			print(secret)
		!`
		echo -n "$key" > $keyfile 
		exit
	else
		echo "$prog: re-run with -i to initialise for use" >&2
		exit 1
	fi
fi
export EMCLI_USERNAME_KEY=`cat $keyfile`

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

if ! which emcli >/dev/null 2>&1
then
	echo "$prog: emcli not in PATH" >&2
	exit 1
fi

if [ ! -d $ORACLE_HOME/bin/emcliext ]
then
	echo "$prog: directory $ORACLE_HOME/bin/emcliext does not exist" >&2
	exit 1
	# $ORACLE_HOME/bin/emcliext/__pycache__ for compiled stuff
fi

if [ ! -r $MODULEDIR/$file.py ] 
then
	echo "$prog: cannot find module '$file'" >&2
	exit 1
fi

emcli @$MODULEDIR/$file.py $*
