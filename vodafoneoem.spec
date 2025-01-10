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
%{_libdir}/*
%{_sysconfdir}/profile.d/*
%{_sysconfdir}/firewalld/services/*
%{_libexecdir}/*


%changelog

