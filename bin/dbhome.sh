#!/usr/bin/sh
#
# $Header: buildtools/scripts/dbhome.sh /linuxamd64/2 2010/10/01 07:11:28 aime Exp $ dbhome.sh.pp Copyr (c) 1991 Oracle
#
###################################
# 
# usage: ORACLE_HOME=`dbhome [SID]`
# NOTE:  A NULL SID is specified with "" on the command line
#
# The only sane way to use this script is with SID specified on the 
# command line or to have ORACLE_SID set for the database you are looking
# for.  The return code will be 1 if dbhome can't find ANY value, 2 if
# it finds a questionable value, 0 if it finds a good one (ie. out of
# oratab).
#
# If ORACLE_SID is set or provided on the command line the script
# will write to the standard output the first of the following that
# it finds:
#	1.  The value of the 2nd field in oratab where the
#	    value of the 1st field equals $ORACLE_SID.
#	2.  The home directory for the user 'oracle' in /etc/passwd
#	    or in the yellow pages password entries.
#
# If ORACLE_SID is not set and not provided on the command line the 
# script will write to the standard output the first of the following
# that it finds:
#	1.  The current value of ORACLE_HOME if not null.
#	2.  The home directory for the user 'oracle' in /etc/passwd
#	    or in the yellow pages password entries.
#
# This script currently uses no hard-coded defaults for ORACLE_SID or
# ORACLE_HOME.
#
#####################################

case "$ORACLE_TRACE" in
    T)	set -x ;;
esac

trap '' 1

RET=0
ORAHOME=""
ORASID=${ORACLE_SID-NOTSET}
ORASID=${1-$ORASID}

ORATAB=/etc/oratab

PASSWD=/etc/passwd
PASSWD_MAP=passwd.byname

case "$ORASID" in
    NOTSET)	# ORACLE_SID not passed in and not in environment
		RET=2
		ORAHOME="$ORACLE_HOME" ;;

    *)	# ORACLE_SID was set or provided on the command line
        if test -f $ORATAB ; then
	    # Try for a match on ORASID in oratab
	    # NULL SID is * in oratab
	    case "$ORASID" in
		"")	ORASID='\*' ;;
	    esac

	    ORAHOME=`awk -F: '{if ($1 == "'$ORASID'") {print $2; exit}}' \
			$ORATAB 2>/dev/null`
	fi ;;
esac

case "$ORAHOME" in
    "")	# Not found in oratab or ORACLE_HOME not set;
   	# try /etc/passwd & yp for "oracle"
	RET=2
        ORAHOME=`awk -F: '/^oracle:/ {print $6; exit}' $PASSWD`
	case "$ORAHOME" in

	    "")	ORAHOME=`(ypmatch oracle $PASSWD_MAP) 2>/dev/null | \
		    awk -F: '/^oracle:/ {print $6; exit}'`

		case "$ORAHOME" in
		    "")	echo "Cannot locate ORACLE_HOME." 1>&2
			exit 1 ;;
		esac ;;
	esac ;;
esac

echo $ORAHOME
exit $RET
