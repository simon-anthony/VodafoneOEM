# OEM Deployment Tools 

Tools to support OEM activities.


## Overview

This package aims to simplify deployment, execution and developement of Python modules and
libraries for use in adminsterting Oracle Enterprise Manager activities.

### Examples

We use a wrapper, *emrun*, to invoke programs from our catalogue. To list the modules
installed:

#### List all installed modules
<pre class=console><code>$ <b>emrun -l</b>
create_gold_agent_image
create_group
get_add_host_status
get_targets
promote_cluster
promote_discovered_targets
promote_gold_agent_image
submit_add_host
update_group_of_agents 
...
</code></pre>

#### To get help on an individual module
<pre class=console><code>$ <b>emrun -- update_group_of_agents -h</b>
usage: update_group_of_agents [-h] [-o OMS] [-u USERNAME] -p PASSWORD -g GROUP
                              -i IMAGE [-v]

Update a group of agents

optional arguments:
  -h, --help            show this help message and exit
  -o OMS, --oms OMS     URL
  -u USERNAME, --username USERNAME
                        sysman user
  -p PASSWORD, --password PASSWORD
                        sysman password
  -g GROUP, --group GROUP
                        group
  -i IMAGE, --image IMAGE
                        gold agent image name
  -v, --validate_only   check whether agents can be updated
</code></pre>

#### Further examples
Having set the following:
<pre><code>user=sysman
oms=https://oms.example.com:7803
password=Naxy7839 
</code></pre>

We can then performa tasks like:

#### Create a Gold Agent Image
<pre class=console><code>$ <b>emrun -- create_gold_agent_image -u $user -o $oms -p $password \
    -s oel.example.com \
    -v AGENT_RU24 \
    -d "Base Agent Image for RU24" \
    -i DB_MONITORING</b>
</code></pre>

#### Add a Number of Hosts
<pre class=console><code>$ <b>emrun -- submit_add_host -u $user -o $oms -p $password \
-d example.com \
    -i DB_MONITORING \
    -c 'NC-ORACLE' \
    -w \
    oim rhl mon</b>
</code></pre>


### Prerequisites

#### Linux Packages
Additional packages may be required.

They will be automatically installed if the repositories are available.
Otherwise download these packages and install them beforehand.

## Installing from Packages

To download the latest RPM packages and review release notes, see the [VODAFONEoem releases](https://github.com/simon-anthony/vodafone/releases) page.

Install the package with the usual RPM based tools: `rpm`, `yum` or `dnf`.

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. 


## Developing
To develop the package clone or download the repository.
GNU Autotools are required for development.

#### GNU Autotools
The [GNU Autotools](https://en.wikipedia.org/wiki/GNU_Autotools) are required
to build and deploy the source packages. 

From Linux these can be installe with yum/dnf:

* autoconf
* automake
* libtool

## Building RPMS from the Source Tree
Set `%_topdir` in the file `$HOME/.rpmmacros`. For example:

* `%_topdir %{getenv:HOME}/.rpm`

Next run the build script:

* `./build.sh`

The RPM file will be created at, for example:

* `%_topdir/RPMS/noarch/vodafoneoem-1.1-1.el9.noarch.rpm`

Where 1.1 is the version and 1 is the release.

Which you can then copy or move as you see fit and install with <b>rpm</b>(8), <b>dnf</b>(8) or <b>yum</b>(8). For example:

<pre class=console><code># <b>dnf -y install vodafoneoem-1.1-1.el9.noarch.rpm</b>
</code></pre>

To remove the currently installed package version:

<pre class=console><code># <b>dnf -y remove vodafoneoem</b>
</code></pre>

## Releases and Versions

In the `.spec` file can be found the _version_ and _release_:

```console
Version:    1.1
Release:    1
```

A _version_ of software may change should new programs be added, functionality enhanced, APIs changed or any such enhancement or modification of its behaviour occur.

A _release_ would change (incremented) when there is a change in the way the product is
packaged or delivered (for example, post installation scripts) or its
dependencies change. The release would be reset to 1 when a new _version_ of
the software is built. It is, in effect, the number of times this version of the software was released. 


### Version Changes

When you wish to freeze a version of the software and commit the changes, do
the following:

#### Change the .spec File 

Change the Version to that which is desired, for example, to create version
1.2:

<pre class=console><code>Version:    <b>1.2</b>
Release:    1
</code></pre>

#### Change the configure.ac file

The corresponding version must also be changed in the arguments to the
`AC_INIT()` macro in the `configure.ac` file:

<pre class=console><code>AC_INIT([vodafoneoem],[<b>1.2</b>],[bugs@vodafone.com])
</code></pre>

##### Ensure that all changes are committed

Check commits:
<pre class=console><code>$ <b>git status -u</b>
</code></pre>

If ncessary, commit:
<pre class=console><code>$ <b>git commit -a -m "Version 1.2 Release 1"</b> 
</code></pre>

<pre class=console><code>$ <b>git push -u origin main"</b> 
</code></pre>

#### Tag the commit with the Version and Rlease
<pre class=console><code>$ <b>git tag 1.2-1"</b> 


### Build Steps

You don't need to run these if you use the build script, however, these are
shown for completeness.  The build script completes the following steps.

Create the build directories:

<pre><code>for dir in BUILD BUILDROOT RPMS SOURCES SPECS SRPMS
do
    mkdir -p $topdir/$dir
done
</code></pre>

Bootstrap the **autoconf** tools:

* `autoreconf --install`

Then run configure:

* `./configure`

This will create the necsessary <code>Makefile</code> that is required to build the source tarball.
Then we can create the tarball:

* `make dist-gzip`

We can then move the package into the `SOURCES` directory:

* `mv vodafoneoem-`*vers*`.tar.gz $topdir/SOURCES`

And we also need a copy the spec file to the `SPECS` directory:

* `cp -f vodafoneoem.spec $topdir/SPECS`

Finally, build the package:

* `rpmbuild -bb $topdir/SPECS/vodafoneoem.spec`

The RPM file will be created at:

<pre>%\_topdir/RPMS/noarch/vodafoneoem-<i>m</i>.<i>n</i>-<i>r</i>.el9.noarch.rpm</pre>


## Installing from a Tar Bundle

Download the latest release.

Unzip the package:

<pre>
tar xzf vodafoneoem-<i>m</i>.<i>n</i>.tar.gz
</pre>

Run `configure`:

```
./configure 
```

If desired to specify an installation destination other than `/usr/local` do so
with the usual configure mechanism:

```
./configure --prefix=/opt/VODAFONEtools 
```

Build the software:
* `make`

and then install it:
* `make install`

### Configuring

Ensure that the *bindir* path derived from the install *prefix* in the `configure`
step is available in the `PATH` environment variable. Using the previous example where the default of `/user/local/bin` is not chosen:

<pre>
PATH=$PATH:/opt/VODAFONEoem/bin
</pre>

## Authors

* **Simon Anthony** - *Initial work* - * [Simon Anthony](https://github.com/simon-anthony)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

