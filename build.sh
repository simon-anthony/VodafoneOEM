# vim: syntax=sh:sw=4:ts=4:
topdir=`eval echo \`sed -n '
    /^%_topdir/ {
        s;%_topdir[     ]*;;
        s;%{getenv:HOME};$HOME; 
        p
    }' ~/.rpmmacros\``

[ "X$topdir" != "X" ] || { echo "ERROR: _topdir not set in .rpmmacros" >&2; exit 1; }

echo topdir is $topdir

for dir in BUILD BUILDROOT RPMS SOURCES SPECS SRPMS
do
	mkdir -p $topdir/$dir
done

autoreconf --install || exit
./configure

pkg=`sed -n 's;.*AC_INIT(\[\([^,]*\)\].*;\1;p' configure.ac`
vers=`sed -n 's;.*AC_INIT(\[\([^,]*\)\],[   ]*\[\([^,]*\)\].*;\2;p' configure.ac`

make dist-gzip || exit $?  # make dist-gzip PACKAGE=$pkg || exit $?

mv $pkg-$vers.tar.gz $topdir/SOURCES

cp -f $pkg.spec $topdir/SPECS

rpmbuild -D "_package $pkg" -bb $topdir/SPECS/$pkg.spec

# When creating a new tag, don't forget to push it:
# git log --oneline
# git tag
# git tag 1.4-1
# git push --tags
#
# Cleanup:
# sudo dnf -y -C remove --noautoremove vodafoneoem
# sudo rpm -e --nodeps --noscripts vodafoneoem
# Install without cache:
# sudo dnf install -C -y -v ~/.rpm/RPMS/noarch/vodafoneoem-1.2-1.el9.noarch.rpm
