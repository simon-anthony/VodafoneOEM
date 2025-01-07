#!/usr/bin/sh

# This script is not intended to be run directly by the user

[ $DBUS_SESSION_BUS_ADDRESS ] || { echo "$PROG: DBUS_SESSION_BUS_ADDRESS not set" >&2; exit 1; }

read -rsp "Enter login password:" password
echo
read -rsp "Re-enter login password:" rpassword
echo
if [ "X$password" != "X$rpassword" ]
then
	echo "$PROG: passwords do not match" >&2
	exit 1
fi
echo "$PROG: creating keyring..." 
echo -n "$password" | gnome-keyring-daemon --unlock
