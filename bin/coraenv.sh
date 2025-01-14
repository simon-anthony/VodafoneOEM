#!/usr/bin/sh
###################################
# 
# $Header: buildtools/scripts/coraenv.sh /linuxamd64/3 2012/02/06 07:01:35 vdandu Exp $ coraenv
# 
# Copyright (c) 1987, 2012, Oracle and/or its affiliates. All rights reserved. 
#
# This routine is used to condition a C shell user's environment
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
#	ORACLE_SID	Oracle system identifier
#	ORACLE_HOME	Top level directory of the Oracle system hierarchy
#	PATH		Old ORACLE_HOME/bin removed, new one added
#       ORACLE_BASE     Top level directory for storing data files and 
#                       diagnostic information.
#
# usage: source /usr/local/coraenv
#
#####################################

#
# Set minimum environment variables
#

# 'source' on /usr/bin/csh under HP can't pass additional arguments.
# So just look for ORAENV_SILENT set in the environment to avoid creating output
if ($?ORAENV_SILENT == 0 ) then
    set ORAENV_SILENT=NO             
endif

if ($?ORACLE_SID == 0) then

    set ORASID=$LOGNAME
else
    set ORASID=$ORACLE_SID
endif
if ("$ORASID" == '' ) set ORASID='*'

if ($?ORAENV_ASK == 0 ) then
	set ORAENV_ASK=YES		#ORAENV_ASK suppresses prompt when set
endif

if ($ORAENV_ASK != NO ) then
    echo -n "ORACLE_SID = [$ORASID] ? "
    set READ=($<)

    if ("$READ" != '') set ORASID="$READ"
endif
if ("$ORASID" == '*') set ORASID=""
setenv ORACLE_SID "$ORASID"

if ($?ORACLE_HOME == 0) then
    set OLDHOME=$PATH		#This is just a dummy value so a null OLDHOME
else				#can't match anything in the switch below
    set OLDHOME=$ORACLE_HOME
endif

set ORAHOME=`dbhome "$ORASID"`
if ($status == 0) then
    setenv ORACLE_HOME $ORAHOME
else
    echo -n "ORACLE_HOME = [$ORAHOME] ? "
    set NEWHOME=$<

    if ($NEWHOME == "") then
	setenv ORACLE_HOME $ORAHOME
    else
	setenv ORACLE_HOME $NEWHOME
    endif
endif

#
# Reset LD_LIBRARY_PATH
#
if ($?LD_LIBRARY_PATH == 0) then
    setenv LD_LIBRARY_PATH $ORACLE_HOME/lib
else
    switch ($LD_LIBRARY_PATH)
    case *$OLDHOME/lib* :
        setenv LD_LIBRARY_PATH \
	    `echo $LD_LIBRARY_PATH | sed "s;$OLDHOME/lib;$ORACLE_HOME/lib;g"`
        breaksw
    case *$ORACLE_HOME/lib* :
        breaksw
    case "" :
        setenv LD_LIBRARY_PATH $ORACLE_HOME/lib
        breaksw
    default :
        setenv LD_LIBRARY_PATH $ORACLE_HOME/lib:${LD_LIBRARY_PATH}
        breaksw
    endsw
endif

#
# Adjust path accordingly
#

switch ($PATH)
case *$OLDHOME/bin* :
    setenv PATH `echo $PATH | sed "s;$OLDHOME/bin;$ORACLE_HOME/bin;g"`
    breaksw
case *$ORACLE_HOME/bin* :
    breaksw
case *[:] :
    setenv PATH ${PATH}$ORACLE_HOME/bin:
    breaksw
case "" :
    setenv PATH $ORACLE_HOME/bin
    breaksw
default :
    setenv PATH ${PATH}:$ORACLE_HOME/bin
    breaksw
endsw

unset ORASID ORAHOME OLDHOME NEWHOME READ

# Set the value of ORACLE_BASE in the environment.
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
#  $ORACLE_HOME.

set ORABASE_EXEC=$ORACLE_HOME/bin/orabase

if ($?ORACLE_BASE != 0) then
   set OLD_ORACLE_BASE=$ORACLE_BASE
   unsetenv ORACLE_BASE
else
   set OLD_ORACLE_BASE=""
endif

if ( -w $ORACLE_HOME/inventory/ContentsXML/oraclehomeproperties.xml ) then
   if (-f $ORABASE_EXEC) then
      if (-x $ORABASE_EXEC) then
         set BASEVAL=`$ORABASE_EXEC`
         setenv ORACLE_BASE $BASEVAL

         # did we have a previous value for ORACLE_BASE
         if ($OLD_ORACLE_BASE != "") then
            if ( $OLD_ORACLE_BASE != $ORACLE_BASE ) then
               if ( $ORAENV_SILENT != "true" ) then
                  echo "The Oracle base has been changed from $OLD_ORACLE_BASE to $ORACLE_BASE"
               endif
            else
               if ( $ORAENV_SILENT != "true" ) then
                  echo "The Oracle base remains unchanged with value $OLD_ORACLE_BASE"
               endif
            endif
         else
            if ( $ORAENV_SILENT != "true" ) then
               echo "The Oracle base has been set to $ORACLE_BASE"
            endif
         endif
      else
         if ( $ORAENV_SILENT != "true" ) then
            echo "The $ORACLE_HOME/bin/orabase binary does not have execute privilege"
            echo "for the current user, $USER.  Rerun the script after changing"
            echo "the permission of the mentioned executable."
            echo "You can set ORACLE_BASE manually if it is required."
         endif
      endif
   else
      if ( $ORAENV_SILENT != "true" ) then
         echo "The $ORACLE_HOME/bin/orabase binary does not exist"
         echo "You can set ORACLE_BASE manually if it is required."
      endif
   endif
else
   if ( $ORAENV_SILENT != "true" ) then
      echo "ORACLE_BASE environment variable is not being set since this"
      echo "information is not available for the current user ID $USER."
      echo "You can set ORACLE_BASE manually if it is required."
   endif
endif

if ($?ORACLE_BASE == 0) then
    if ( $ORAENV_SILENT != "true" ) then
          echo "Resetting ORACLE_BASE to its previous value or ORACLE_HOME";
    endif
    if ( "$OLD_ORACLE_BASE" != "" ) then
         if ( $ORAENV_SILENT != "true" ) then
             echo "The Oracle base remains unchanged with value $OLD_ORACLE_BASE";
         endif
         set BASE_VAL=$OLD_ORACLE_BASE ;
    else
         if ( $ORAENV_SILENT != "true" ) then
             echo "The Oracle base has been set to $ORACLE_HOME";
         endif
         set BASE_VAL=$ORACLE_HOME ;
    endif
    setenv ORACLE_BASE $BASE_VAL
endif

unset ORAENV_SILENT OLD_ORACLE_BASE

#
# Install local modifications here
#

