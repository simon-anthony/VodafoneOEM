%define _prefix /usr/local

Name:		vodafoneoem
Version:	1.1
Release:	1%{?dist}
Summary:	Utilities for OEM Management

Group:		Productivity/Database/Tools
License:	GPL
URL:		www.oracle.com
Vendor:		SA
Packager:	Simon Anthony
Source0:	%{name}-%{version}.tar.gz

#Requires: jq, libnotify, bash, bind-utils
Requires: bash, python3
BuildRequires: bash, python3, autoconf, automake

BuildArch: noarch

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

%preun


%files
%{_bindir}/*
%{_prefix}/lib/*
%{_sysconfdir}/*
%{_libexecdir}/*


%changelog

