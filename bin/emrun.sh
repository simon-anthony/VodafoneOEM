#!/usr/bin/sh -

emcli=`which emcli 2>&-`
PATH=/usr/bin:@BINDIR@ export PATH
prog=`basename $0 .sh`
export PROG=$prog

export MODULEDIR=@LIBEXECDIR@/@PACKAGE@
export PYTHONPATH=@LIBDIR@/python@PYTHON_VERSION@ # not actually used by EMCLI Jython
# EMCLI_PYTHONPATH is for modules (i.e. libraries) but does not appear to work...
export EMCLI_PYTHONPATH=@LIBDIR@/python@PYTHON_VERSION@

prog=`basename $0 .sh`

usage() {
    cat >&2 <<-!
		usage: $prog {-l|-k[-f]|-i|-u <username>} [-v]
		usage: $prog [-s <sid>] -e [-v]
		usage: $prog [-s <sid>] [-v] -- <module> [-h|--help] [<args>]
		OPTION:
		  -l, --list                 List <module>s
		  -k, --keyring              Create keyring
		  -f, --force                Force overwite of existing keyring, requires -k
		  -i, --initialise           Initialise keystore for use by creating key token
		  -u, --username=NAME        Set username (and enter password) for OMS in keystore
		  -s, --sid=NAME             Set ORACLE_HOME (OMS/Agent) for NAME
		  -e, --emcliext             Link extension modules in ORACLE_HOME, requires -s
		  -v, --verbose              Verbose 
		  -?, --help                 Give this help list
	!
    exit 2
}

TEMP=`getopt -o ls:ekiu:fvh --long list,sid,emcliext,keyring,initialise,username,force,verbose,help \
     -n "$prog" -- "$@"`

[ $? != 0 ] && { usage; exit 1; }

# Note the quotes around `$TEMP': they are essential!
eval set -- "$TEMP"
typeset lflg= sflg= eflg= kflg= fflg= iflg= vflg= hflg= errflg=  

while true
do
	case "$1" in
	-l|--list)
		lflg=y
		shift ;;
	-s|--sid)
		sflg=y
		sid=$2
		[ -r @SYSCONFDIR@/profile.d/setoraenv.sh ] && \
			. @SYSCONFDIR@/profile.d/setoraenv.sh
		shift 2 ;;
	-e|--emcliext)
		eflg=y
		shift ;;
	-k|--keyring)
		kflg=y
		[ "$iflg" -o "$uflg" ] && errflg
		shift ;;
	-f|--force)
		fflg=y
		shift ;;
	-i|--initialise)
		iflg=y
		[ "$kflg" -o "$uflg" ] && errflg
		shift ;;
	-u|--username)
		uflg=y
		[ "$kflg" -o "$iflg" ] && errflg
		username=$2
		shift 2 ;;
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
		ls $MODULEDIR/*.py | xargs basename -s .py
	fi
	exit
fi

[ $# -eq 0 -a \( -z "$kflg" -a -z "$uflg" -a -z "$iflg" -a -z "$eflg" \) ] && errflg=y
[ "$fflg" -a -z "$kflg" ] && errflg=y	# -f requires -k

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
		exec @BINDIR@/unlock-keyring
	else
		exec dbus-run-session -- @BINDIR@/unlock-keyring
	fi
fi

if ! [ -r $HOME/.local/share/keyrings/login.keyring ]
then
	# Keys are in $HOME/.local/share/keyrings/user.keystore 
	echo "$prog: login keyring does not exist, re-run with -k" >&2
	exit 1
fi

# Check keyfile

keyfile=$HOME/.config/emcli/username.key 
mkdir -p `dirname $keyfile`

if [ ! -r $keyfile ]	# Create a key
then
	if [ $iflg ]
	then
		echo "$prog: creating key" 
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

if [ $uflg ]
then
	[ $DBUS_SESSION_BUS_ADDRESS ] || { echo "$PROG: DBUS_SESSION_BUS_ADDRESS not set" >&2; exit 1; }

	if python <<-!
		import keyring
		import os
		import getpass
		import sys

		username = '$username'
		password =  getpass.getpass(prompt='Enter password for ' + username + ': ')

		EMCLI_USERNAME_KEY = os.getenv('EMCLI_USERNAME_KEY')

		service_id = 'emcli'
		try:
		    keyring.set_password(service_id, username, password)
		    keyring.set_password(service_id, EMCLI_USERNAME_KEY, username)
		except:
		    sys.exit(1)

		sys.exit(0)
	!
	then
		echo "$prog: username/password set"
		exit
	else
		echo "$prog: failed to set username/password, check keyring"
		exit 1
	fi
fi

if [ $sflg ] # set ORACLE_HOME
then
	setoraenv -s $sid || exit
fi

if [ "X$emcli" = "X" -a -z "$ORACLE_HOME" ]
then
	echo "$prog: cannot find emcli, try -s" >&2
	exit 1
fi

if [ "X$emcli" = "X" ]
then
	if [ -x $ORACLE_HOME/bin/emcli ]
	then
		emcli=$ORACLE_HOME/bin/emcli
	elif [ -x $ORACLE_HOME/emcli ]
	then
		emcli=$ORACLE_HOME/emcli
		echo "$prog: emcli not in PATH or ORACLE_HOME" >&2
		exit 1
	fi
fi
export EMCLI_DIR=`dirname $emcli`
PATH=$PATH:$EMCLI_DIR

if [ $eflg ]
then
	if [ ! -x $EMCLI_DIR/emcli ]
	then
		echo "$prog: $EMCLI_DIR/emcli does not exist" >&2
		exit 1
	fi
	if [ ! -d $EMCLI_DIR/emcliext ]
	then
		mkdir $EMCLI_DIR/emcliext || exit
	fi
	typeset -i count=0
	for module in `grep -l '^# emcliext' $MODULEDIR/*.py`
	do
		[ $count -eq 0 ] && echo -n "$prog: installing extension module: "
		echo -n "`basename $module .py` "
		ln -fs $module $EMCLI_DIR/emcliext/`basename $module` 
		(( count += 1 ))
	done
	echo
	exit 
fi

if [ "$SSH_TTY" ]
then
	n=`egrep -c -e '^[[:blank:]]*auth[[:blank:]]+optional[[:blank:]]+pam_gnome_keyring.so' \
			-e '^[[:blank:]]*password[[:blank:]]+optional[[:blank:]]+pam_gnome_keyring.so[[:blank:]]+use_authtok' \
			-e '^[[:blank:]]*session[[:blank:]]+optional[[:blank:]]+pam_gnome_keyring.so[[:blank:]]+auto_start' /etc/pam.d/sshd`
	if [ $n -ne 3 ]
	then
		echo "$prog: pam_gnome_keyring.so entries missing or incomplete for sshd" >&2
		exit 1
	fi
fi

# Now run module

file=`basename $1 .py`
shift

if [ ! -d $EMCLI_DIR/emcliext ]
then
	echo "$prog: directory $EMCLI_DIR/emcliext does not exist" >&2
	exit 1
fi

if [ ! -r $MODULEDIR/$file.py ] 
then
	echo "$prog: cannot find module '$file'" >&2
	exit 1
fi

emcli @$MODULEDIR/$file.py $*
