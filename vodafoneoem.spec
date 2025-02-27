%define _prefix /usr/local

Name:		%(sed -n '/AC_INIT/ s;.*\[\(.*\)\],.*,.*;\1;p' configure.ac)
Version:	%(sed -n '/AC_INIT/ s;.*,\[\(.*\)\],.*;\1;p' configure.ac)
Release:	1%{?dist}
Summary:	Utilities for OEM Management

Group:		Productivity/Database/Tools
License:	GPL
URL:		www.vodafone.com
Vendor:		SA
Packager:	Simon Anthony
Source0:	%{name}-%{version}.tar.gz

Requires: bash, python3, python3-keyring, gnome-keyring, gnome-keyring-pam
BuildRequires: bash, python3, autoconf, automake


%global debug_package %{nil}

%description
Supporting scripts and tools for Oracle Enterprise Manager deployment


%prep
%setup -q


%build
%configure \
	--prefix=%{_prefix} \
	--bindir=%_bindir \
	--sbindir=%_sbindir \
	--datadir=%_datadir \
	--sysconfdir=%_sysconfdir \
	--libdir=%_libdir \
	--includedir=%_includedir \
	--localstatedir=%{_localstatedir} \
	--libexecdir=%{_libexecdir} \
	--mandir=%{_prefix}/share/man 
make %{?_smp_mflags}


%install
[ %buildroot != "/" ] && rm -rf %buildroot
make DESTDIR=%buildroot install


%clean
[ %buildroot != "/" ] && rm -rf %buildroot


%post
for file in region node properties
do
	if [ ! -f %{_datadir}/%{_package}/$file.ini ]
	then
		cp %{_datadir}/%{_package}/$file.ini.example %{_datadir}/%{_package}/$file.ini
	fi
done


%preun
cp -p %{_bindir}/oraenv %{_bindir}/oraenv.bak
cp -p %{_bindir}/coraenv %{_bindir}/coraenv.bak
cp -p %{_bindir}/dbhome %{_bindir}/dbhome.bak


%postun
mv %{_bindir}/oraenv.bak %{_bindir}/oraenv
mv %{_bindir}/coraenv.bak %{_bindir}/coraenv
mv %{_bindir}/dbhome.bak %{_bindir}/dbhome


%files
%{_bindir}/nbread
%{_bindir}/emrun
%{_bindir}/unlock-keyring
%{_bindir}/oemportscan
%{_bindir}/getcreds
%{_bindir}/oraenv
%{_bindir}/dbhome
%{_bindir}/coraenv
%attr(4750,oracle,oinstall)      %{_bindir}/oratab
%{_libdir}/*
%{_sysconfdir}/profile.d/*
%{_sysconfdir}/firewalld/services/*
%{_libexecdir}/*
%attr(1775,oracle,oinstall)		%{_datadir}/%{_package}
%attr(0644,root,root)			%{_datadir}/%{_package}/magic
%attr(0644,root,root)			%{_datadir}/%{_package}/*.example
%{_mandir}/man?/*


%changelog

