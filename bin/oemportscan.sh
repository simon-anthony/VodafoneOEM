#!/usr/bin/sh -
PATH=/usr/bin:/usr/sbin export PATH
prog=`basename $0 .sh`

typeset fflg= gflg= uflg= lflg= errflg= opt=
typeset service="oem"

while getopts f:gul opt 2>/dev/null
do
	case $opt in
	f)	fflg=y	# firewalld service name
		service="$OPTARG"
		;;
	g)	gflg=y	# generate servicesdb file
		[ $lflg ] && errflg=y
		;;
	u)	uflg=y	# list UDP ports also
		[ $lflg ] && errflg=y
		;;
	l)	lflg=y	# listening ports on local host
		[ "$gflg" -o "$uflg"  ] && errflg=y
		;;
	\?)	errflg=y
	esac
done
shift `expr $OPTIND - 1`

[ $# -eq 0 -a ! "$lflg" ] && errflg=y

[ $errflg ] && {
    echo "usage: $prog [-g] [-f <name>] <hostname>..." >&2;
    echo "       $prog -l [-f <name>]" >&2;
    exit 2;
}

if [ "`id -un`" != "root" ]
then
	echo "$prog: must be run as 'root'" >&2
	exit 1
fi

if [ "$gflg" -o "$lflg" ]
then
	servicedb=`mktemp` || exit
fi
service=`basename $service .xml`

if [ ! -r /etc/firewalld/services/$service.xml ]
then
	echo "$prog: cannot open /etc/firewalld/services/$service.xml" >&2; 
	exit 1
fi

if [ $lflg ]
then
	eval declare -A listen=(`ss -l -t4 -n  | awk '$1 == "LISTEN" { split($4, a, ":"); printf("[%s]=1 ", a[2]); }'`)

	awk '/port=/ { match($0, /.*port="([0-9]+).*<!--([^0-9]+).*/, a);
		print a[1] a[2]
	}
	' /etc/firewalld/services/$service.xml |
	while read port comment
	do
		[ -n "${listen[$port]}" ] && { _p=32; ok="OK"; } || { _p=31; ok="  "; }
		[ -t ] && echo -e "\033[${_p}m${port}\033[0m" \"$comment\" \
			   || echo -e "$port" "[$ok]" \"$comment\" 
	done
	exit 
fi

ports=`awk -v servicedb=$servicedb '
	/port=/ { match($0, /.*port="([0-9]+).*<!--.*[[:blank:]]+([^[:blank:]]+)[[:blank:]]+-->/, a);
		ports = sprintf("%s%s%s", ports, sep, a[1]);
		sep = ",";
		if (length(servicedb) > 0 )
			printf("%s	%d/tcp\n", a[2], a[1]) >> servicedb
	 }
	END { print ports; }
' /etc/firewalld/services/$service.xml`


filter() {
	awk '
		/^PORT/,/^$/ {
			if ($0 ~ /^$/)
				next
			if ($1 ~ /^[1-9]/) {
				if ($2 ~ /^open/)
					p=32
				else
					p=31
				printf("%-8s \033[%sm%-12s\033[0m %-s\n", $1, p, $2, $3)
			} else 
				printf("%-8s %-12s %-s\n", $1, $2, $3)
		}'
}

if [ $gflg ]
then
	nmap -sT${uflg:+U} --servicedb $servicedb $* | filter
else
	nmap -sT${uflg:+U} -p $ports $*
fi


