SUFFIXES = .sh 

.sh:
	@echo "g/BASEDIR/s;BASEDIR;$(prefix);g" > exscript.$< ;\
	echo "g/SBINDIR/s;SBINDIR;$(sbindir);g" >> exscript.$< ;\
	echo "g/BINDIR/s;BINDIR;$(bindir);g" >> exscript.$< ;\
	echo "g/LIBDIR/s;LIBDIR;$(libdir);g" >> exscript.$< ;\
	echo "g/LIBEXECDIR/s;LIBEXECDIR;$(libexecdir);g" >> exscript.$< ;\
	echo "g/DATADIR/s;DATADIR;$(datadir);g" >> exscript.$< ;\
	echo "g/SYSCONFDIR/s;SYSCONFDIR;$(sysconfdir);g" >> exscript.$< ;\
	echo "g/LOCALSTATEDIR/s;LOCALSTATEDIR;$(localstatedir);g" >> exscript.$< ;\
	echo "g/PACKAGE/s;PACKAGE;$(PACKAGE);g" >> exscript.$< ;\
	echo "g/PREFIX/s;PREFIX;$(prefix);g" >> exscript.$< ;\
	echo "g/PYTHON_VERSION/s;PYTHON_VERSION;$(PYTHON_VERSION);g" >> exscript.$< ;\
	echo "w! $@" >> exscript.$< 
	@ex -s $< < exscript.$<
	@rm -f exscript.$<
	@chmod +x $@

bin_SCRIPTS = \
	emrun

CLEANFILES = $(bin_SCRIPTS)

EXTRA_DIST = \
	emrun.sh
