#ident $Header$
# vim:syntax=sh:sw=4:ts=4:
################################################################################
# setoraenv: interactive invocation of oraenv
#
################################################################################
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License or, (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not see <http://www.gnu.org/licenses/>>
#

function setoraenv {
	typeset -r prog="setoraenv"
	local iflg= sflg= opt= errflg= OPTIND=1
	local oracle_sid=
	
	while getopts "is:" opt 2>&-
	do
		case $opt in
		i)	iflg=y
			[ $sflg ] && errflg=y
			;;
		s)	sflg=y	
			oracle_sid="$OPTARG"
			[ $iflg ] && errflg=y
			;;
		\?)	errflg=y
		esac
	done
	shift $(( OPTIND - 1 )) 

	[ $# -eq 0 ] || errflg=y

	[ $errflg ] && { echo "usage: $prog [-i|-s <sid>]" >&2; return 2; }

	local oratab=`ls /etc/oratab /var/opt/oracle/oratab 2>&-`

    [ -x /usr/local/bin/oraenv ] || { echo "$prog: no oraenv in local bin" >&2; return 1; }
	[ -n "$oratab" -a -r "$oratab" ] || { echo "$prog: no oratab" >&2; return 1; }

	if [ $iflg ]
	then
		[ -x /usr/local/bin/ckitem ] || { echo "$prog: valtools package not installed" >&2; return 1; }
		local file=`mktemp`

		awk -F: '
			/^[ ]*#/ { next; }
			$1 ~ /[A-Za-z0-9]+/ { printf("%s\t%s\n", $1, $2); }' /etc/oratab > $file

		oracle_sid=`ckitem -u -p "Choose an instance" -f $file` || return
		rm -f $file
	elif [ $sflg ]
	then
        oracle_sid=`awk -F: '$1 == "'$oracle_sid'" { printf("%s", $1); quit; }' $oratab`
	else # pick first enabled entry
        oracle_sid=`awk -F: '$1 ~ /^[a-zA-Z]/ && $3 == "Y" { printf("%s", $1); quit; }' $oratab`
	fi
	if [ -n "$oracle_sid" ]
	then 
		export ORACLE_SID="$oracle_sid" ORAENV_ASK=NO
		. oraenv 
	else
		echo "$prog: specified SID not in $oratab"
		return 1
	fi
	[ -f $ORACLE_HOME/dbs/spfile$ORACLE_SID.ora ] || unset ORACLE_SID # is instance local?
}
typeset -fx setoraenv
