AC_INIT([vodafoneoem],[1.3],[bugs@vodafone.com])
AM_INIT_AUTOMAKE([-Wall -Werror foreign])
AC_CONFIG_MACRO_DIRS([m4])
AC_PROG_AWK([gawk] nawk awk)
AM_CONDITIONAL([LINUX], [test `uname -s` = Linux] )
AM_CONDITIONAL([SUN], [test `uname -s` = SunOS] )
AM_CONDITIONAL([HPUX], [test `uname -s` = HP-UX] )
AM_CONDITIONAL([AIX], [test `uname -s` = AIX] )
AM_PATH_PYTHON()
AC_CONFIG_HEADERS([config.h])
AC_CONFIG_FILES([
Makefile
bin/Makefile
etc/Makefile
lib/Makefile
lib/python/Makefile
libexec/Makefile
share/Makefile
])
AC_OUTPUT
