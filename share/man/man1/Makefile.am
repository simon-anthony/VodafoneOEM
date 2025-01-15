
dist_man1_MANS = \
	nbread.1 \
	oratab.1m

do_subst = sed -i \
	-e 's;[@]BASEDIR[@];$(prefix);g' \
	-e 's;[@]SBINDIR[@];$(sbindir);g' \
	-e 's;[@]BINDIR[@];$(bindir);g' \
	-e 's;[@]LIBDIR[@];$(libdir);g' \
	-e 's;[@]DATADIR[@];$(datadir);g' \
	-e 's;[@]PKGDATADIR[@];$(pkgdatadir);g' \
	-e 's;[@]LIBEXECDIR[@];$(libexecdir);g'  \
	-e 's;[@]DATADIR[@];$(datadir);g' \
	-e 's;[@]SYSCONFDIR[@];$(sysconfdir);g' \
	-e 's;[@]LOCALSTATEDIR[@];$(localstatedir);g' \
	-e 's;[@]PACKAGE[@];$(PACKAGE);g' \
	-e 's;[@]PREFIX[@];$(prefix);g' \
	-e 's;[@]PYTHON_VERSION[@];$(PYTHON_VERSION);g'

install-data-hook:
	cd $(DESTDIR)/$(man1dir) ;\
	for file in $(dist_man1_MANS) ;\
	do \
		$(do_subst) $$file ;\
	done 


