toolsdir = $(libexecdir)/$(PACKAGE)

dist_tools_DATA = \
	vf_create_gold_agent_image.py \
	create_group.py \
	get_add_host_status.py \
	get_targets.py \
	promote_cluster.py \
	promote_discovered_targets.py \
	vf_promote_gold_agent_image.py \
	submit_add_host.py \
	update_group_of_agents.py \
	utils.py \
	vf_deploy_agent.py \
	vf_run_auto_discovery.py

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

install-data-local:
	for file in $(dist_tools_DATA) ;\
	do \
		echo Editing $$file ;\
		$(do_subst) $$file ;\
	done
	$(MAKE) install-dist_toolsDATA
