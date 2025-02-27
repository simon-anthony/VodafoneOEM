#!/usr/bin/sh
#
# $Header: buildtools/scripts/oraenv.sh /st_buildtools_12.1/1 2014/05/13 23:45:50 ajeetkum Exp $ oraenv.sh.pp Copyr (c) 1991 Oracle
# 
# Copyright (c) 1991, 2014, Oracle and/or its affiliates. All rights reserved.
#
# This routine is used to condition a Bourne shell user's environment
# for access to an ORACLE database.  It should be installed in
# the system local bin directory.
#
# The user will be prompted for the database SID, unless the variable
# ORAENV_ASK is set to NO, in which case the current value of ORACLE_SID
# is used.
# An asterisk '*' can be used to refer to the NULL SID.
#
# 'dbhome' is called to locate ORACLE_HOME for the SID.  If
# ORACLE_HOME cannot be located, the user will be prompted for it also.
# The following environment variables are set:
#
#       ORACLE_SID      Oracle system identifier
#       ORACLE_HOME     Top level directory of the Oracle system hierarchy
#       PATH            Old ORACLE_HOME/bin removed, new one added
#       ORACLE_BASE     Top level directory for storing data files and 
#                       diagnostic information.
#
# usage: . oraenv
#
# NOTE:		Due to constraints of the shell in regard to environment
# -----		variables, the command MUST be prefaced with ".". If it
#		is not, then no permanent change in the user's environment
#		can take place.
#
#####################################
#
# process aruments
#
SILENT=''; 
if [ $# -gt 0 ]; then
 for arg in $@
 do
    if [ "$arg" = "-s" ]; then
        SILENT='true'
    fi
 done
fi

case ${ORACLE_TRACE:-""} in

    T)  set -x ;;
esac

#
# Determine how to suppress newline with echo command.
#
N=
C=
if echo "\c" | grep c >/dev/null 2>&1; then
    N='-n'
else
    C='\c'
fi

#
# Set minimum environment variables
#

# ensure that OLDHOME is non-null
if [ ${ORACLE_HOME:-0} = 0 ]; then
    OLDHOME=$PATH
else
    OLDHOME=$ORACLE_HOME
fi
case ${ORAENV_ASK:-""} in                       #ORAENV_ASK suppresses prompt when set

    NO)	NEWSID="$ORACLE_SID" ;;
    *)	case "$ORACLE_SID" in
	    "")	ORASID=$LOGNAME ;;
	    *)	ORASID=$ORACLE_SID ;;
	esac
	echo $N "ORACLE_SID = [$ORASID] ? $C"
	read NEWSID
	case "$NEWSID" in
	    "")		ORACLE_SID="$ORASID" ;;
	    *)	        ORACLE_SID="$NEWSID" ;;		
	esac ;;
esac
export ORACLE_SID

ORAHOME=`dbhome "$ORACLE_SID"`
case $? in
    0)	ORACLE_HOME=$ORAHOME ;;
    *)	echo $N "ORACLE_HOME = [$ORAHOME] ? $C"
	read NEWHOME
	case "$NEWHOME" in
	    "")	ORACLE_HOME=$ORAHOME ;;
	    *)	ORACLE_HOME=$NEWHOME ;;
	esac ;;
esac

export ORACLE_HOME 

#
# Reset LD_LIBRARY_PATH
#
case ${LD_LIBRARY_PATH:-""} in
    *$OLDHOME/lib*)     LD_LIBRARY_PATH=`echo $LD_LIBRARY_PATH | \
                            sed "s;$OLDHOME/lib;$ORACLE_HOME/lib;g"` ;;
    *$ORACLE_HOME/lib*) ;;
    "")                 LD_LIBRARY_PATH=$ORACLE_HOME/lib ;;
    *)                  LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH ;;
esac

export LD_LIBRARY_PATH

#
# Put new ORACLE_HOME in path and remove old one
#

case "$OLDHOME" in
    "")	OLDHOME=$PATH ;;	#This makes it so that null OLDHOME can't match
esac				#anything in next case statement

case "$PATH" in
    *$OLDHOME/bin*)	PATH=`echo $PATH | \
			    sed "s;$OLDHOME/bin;$ORACLE_HOME/bin;g"` ;;
    *$ORACLE_HOME/bin*)	;;
    *:)			PATH=${PATH}$ORACLE_HOME/bin: ;;
    "")			PATH=$ORACLE_HOME/bin ;;
    *)			PATH=$PATH:$ORACLE_HOME/bin ;;
esac

export PATH 

# Locate "osh" and exec it if found
ULIMIT=`LANG=C ulimit 2>/dev/null`

if [ $? = 0 -a "$ULIMIT" != "unlimited" ] ; then
  if [ "$ULIMIT" -lt 2113674 ] ; then

    if [ -f $ORACLE_HOME/bin/osh ] ; then
	exec $ORACLE_HOME/bin/osh
    else
	for D in `echo $PATH | tr : " "`
	do
	    if [ -f $D/osh ] ; then
		exec $D/osh
	    fi
	done
    fi

  fi

fi

#set the value of ORACLE_BASE in the environment.
#
# Use the orabase executable from the corresponding ORACLE_HOME, since
# the ORACLE_BASE of different ORACLE_HOMEs can be different.
# The return value of orabase will be determined based on the value
# of ORACLE_BASE from oraclehomeproperties.xml as set in the ORACLE_HOME inventory.
#
# If orabase can not determine a value then oraenv returns with either ORACLE_BASE 
# as it was or set ORACLE_BASE to $ORACLE_HOME if it was not set earlier.
# 
#
# The existing value of ORACLE_BASE is used to inform the user if the orabase
# determines the value of ORACLE_BASE. In case, oraenv can not determine a
# value then the user is informed with the previous ORACLE_BASE or with the
# $ORACLE_HOME.

ORABASE_EXEC=$ORACLE_HOME/bin/orabase

if [ ${ORACLE_BASE:-"x"} != "x" ]; then
   OLD_ORACLE_BASE=$ORACLE_BASE
   unset ORACLE_BASE
   export ORACLE_BASE     
else
   OLD_ORACLE_BASE=""
fi

if [ -w $ORACLE_HOME/inventory/ContentsXML/oraclehomeproperties.xml ]; then
   if [ -f $ORABASE_EXEC ]; then
      if [ -x $ORABASE_EXEC ]; then
         ORACLE_BASE=`$ORABASE_EXEC`

         # did we have a previous value for ORACLE_BASE
         if [ ${OLD_ORACLE_BASE:-"x"} != "x" ]; then
            if [ $OLD_ORACLE_BASE != $ORACLE_BASE ]; then
               if [ "$SILENT" != "true" ]; then
                  echo "The Oracle base has been changed from $OLD_ORACLE_BASE to $ORACLE_BASE"
               fi
            else
               if [ "$SILENT" != "true" ]; then
                  echo "The Oracle base remains unchanged with value $OLD_ORACLE_BASE"
               fi
            fi
         else
            if [ "$SILENT" != "true" ]; then
               echo "The Oracle base has been set to $ORACLE_BASE"
            fi
         fi
         export ORACLE_BASE
      else
         if [ "$SILENT" != "true" ]; then
            echo "The $ORACLE_HOME/bin/orabase binary does not have execute privilege"
            echo "for the current user, $USER.  Rerun the script after changing"
            echo "the permission of the mentioned executable."
            echo "You can set ORACLE_BASE manually if it is required."
         fi
      fi
   else
      if [ "$SILENT" != "true" ]; then
         echo "The $ORACLE_HOME/bin/orabase binary does not exist"
         echo "You can set ORACLE_BASE manually if it is required."
      fi
   fi
else
   if [ "$SILENT" != "true" ]; then
      echo "ORACLE_BASE environment variable is not being set since this"
      echo "information is not available for the current user ID $USER."
      echo "You can set ORACLE_BASE manually if it is required."
   fi
fi

if [ ${ORACLE_BASE:-"x"} == "x" ]; then
     if [ "$SILENT" != "true" ]; then
         echo "Resetting ORACLE_BASE to its previous value or ORACLE_HOME";
     fi
     if [ "$OLD_ORACLE_BASE" != "" ]; then
          ORACLE_BASE=$OLD_ORACLE_BASE ;
          if [ "$SILENT" != "true" ]; then
                 echo "The Oracle base remains unchanged with value $OLD_ORACLE_BASE";
         fi 
    else
          ORACLE_BASE=$ORACLE_HOME ;
          if [ "$SILENT" != "true" ]; then
                 echo "The Oracle base has been set to $ORACLE_HOME";
         fi
    fi
    export ORACLE_BASE ;
fi
#
# Install any "custom" code here
#

