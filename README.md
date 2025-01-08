# OEM Deployment Tools 

Tools to support OEM activities.

## Overview

This package aims to simplify deployment, execution and developement of Python modules and
libraries for use in adminsterting Oracle Enterprise Manager activities.

The package provides a general purpose harness, *emrun*, to invoke programs from our catalogue. It also sets up an execution environment that includes password-less login to emcli by exploting the gnome-keyring.

### Passwordless Login

Use is made of the gnome-keyring to afford the saving of credentials used for
OMS login and subsequent password-less invocation.

#### Setup

When not in a desktop environment (for example ssh) use of the keyring requires the following in
the PAM configuration:

<pre class=console><code>$ <b>cat /etc/pam.d/sshd</b>
#%PAM-1.0
auth       substack     password-auth
<b>auth       optional     pam_gnome_keyring.so</b>
auth       include      postlogin
account    required     pam_sepermit.so
account    required     pam_nologin.so
account    include      password-auth
password   include      password-auth
<b>password   optional     pam_gnome_keyring.so use_authtok</b>
# pam_selinux.so close should be the first session rule
session    required     pam_selinux.so close
session    required     pam_loginuid.so
# pam_selinux.so open should only be followed by sessions to be executed in the user context
session    required     pam_selinux.so open env_params
session    required     pam_namespace.so
session    optional     pam_keyinit.so force revoke
session    optional     pam_motd.so
session    include      password-auth
<b>session    optional     pam_gnome_keyring.so auto_start</b>
session    include      postlogin
</code></pre>

#### Creating the Keyring

If the login keyring does not exist it can be created:

<pre class=console><code>$ <b>emrun -k</b>
Enter login password: <b>*******</b>
Re-enter login password: <b>*******</b>
</code></pre>

The password entered must match that used to login when initialising the
keyring for the first time (no check is made). Password changes will
subsequently be synchronised through PAM.

#### Initialising a Key Token 

We store our username/password combination against a token in the keystore. To
initialise this token and save it we

<pre class=console><code>$ <b>emrun -i</b>
emrun: creating key
</code></pre>

#### Saving a Username and Password

Finally, we are ready to save the username and password to be used to login to
OMS. This step can be repeated at any time should this combination change.

<pre class=console><code>$ <b>emrun -u </b><i>username</i>
Enter password for <i>username</i>: <b>********</b>
</code></pre>

### Example Use

The program, *emrun*, to invoke programs from our catalogue. To list the modules
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
  -g GROUP, --group GROUP
                        group
  -i IMAGE, --image IMAGE
                        gold agent image name
  -v, --validate_only   check whether agents can be updated
</code></pre>

#### Further examples
Assuming the following:
<pre><code>oms=https://oms.example.com:7803
</code></pre>

We can then performa tasks like:

#### Create a Gold Agent Image
<pre class=console><code>$ <b>emrun -- create_gold_agent_image -o $oms \
    -s oel.example.com \
    -v AGENT_RU24 \
    -d "Base Agent Image for RU24" \
    -i DB_MONITORING</b>
</code></pre>

#### Add a Number of Hosts
<pre class=console><code>$ <b>emrun -- submit_add_host -o $oms \
    d example.com \
    -i DB_MONITORING \
    -c 'NC-ORACLE' \
    -w \
    oim rhl mon</b>
</code></pre>

## Adding Modules

Additional modules using EMCLI Jython routines can be added to the package:

### Writing a Module
Suppose we create `mymodule.py` in the `libexec` subdirectory. This modules
has the basic structure as follows.

#### Import the Modules/Packages we will use
```Python
import sys
import argparse
from utils import getcreds
```

#### Parse the argument list in the standard way
```Python
parser = argparse.ArgumentParser(
    prog='get_targets',
    description='Retrieve targets of specified type',
    epilog='Text at the bottom of help')

parser.add_argument('-o', '--oms', required=True, help='URL')

group = parser.add_mutually_exclusive_group()
group.add_argument('--host', action='store_true', help='Show agent target types (default)')
group.add_argument('--agent', action='store_true', help='Show host target types')
group.add_argument('--database', action='store_true', help='Show oracle database target types')

# Would not usually pass sys.argv to parse_args() but emcli scoffs argv[0]
args = parser.parse_args(sys.argv)
```

#### Set up the OMS properties
```Python
set_client_property('EMCLI_OMS_URL', args.oms)
set_client_property('EMCLI_TRUSTALL', 'true')
```

#### Retrieve the credentials and login
```Python
creds = getcreds() # returns a dictionary object

login(username=creds['username'], password=creds['password'])
```

#### Invoke the EMCLI verb
Here we perform any additional processing required before or after invocation of
the EMCLI verb. For example, for the verb *get_targets()*:

```Python
# target_type can be oracle_emd, host, oracle_database etc....
target_type = 'host'
if args.agent:
    target_type = 'oracle_emd'
elif args.database:
    target_type = 'oracle_database'

try:
    targets = get_targets(targets='%:'+target_type)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)
    
for target in targets.out()['data']:
    print target['Target Name']
```

### Add to Payload
We then add `mymodule.py` to the *dist_tools_DATA* variable in `Makefile.am`.

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
* rpm-build

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


### Version (and Release) Changes

When you wish to freeze a version of the software and commit the changes, we 
need to change the version number in both the `.spec` and `configure.ac`
files. We make sure that all changes are committed as required and push to the
central repository. Finally we tag the committed code with the version and release and
push the tags to the central repository.

These steps are explained in detail below.

Note that the requirement to change the version number in
both the `.spec` and `configure.ac` files can be reduced to only needing to
change the latter by employing a macro in the former.

#### Change the .spec File 

Change the Version to that which is desired, for example, to create version
1.2:

<pre class=console><code>Version:    <b>1.2</b>
Release:    1
</code></pre>

##### Using a macro
To avoid the need to change two files to update the version number, we can
use RPM's macro feature to extract the version from only the `configure.ac`
file. Our `.spec` file then becomes:

<pre class=console><code>Version:    <b>%(sed -n '/AC_INIT/ s;.*\[\(.*\)\],.*;\1;p' configure.ac)</b>
Release:    1
</code></pre>

And we need only change the version in the file `configure.ac`.

#### Change the configure.ac file

The corresponding version must also be changed in the arguments to the
`AC_INIT()` macro in the `configure.ac` file:

<pre class=console><code>AC_INIT([vodafoneoem],[<b>1.2</b>],[bugs@vodafone.com])
</code></pre>

##### Ensure that all changes are committed

Check commits:
<pre class=console><code>$ <b>git status -u</b>
</code></pre>

If necessary, commit:
<pre class=console><code>$ <b>git commit -a -m "Version 1.2 Release 1"</b> 
</code></pre>

<pre class=console><code>$ <b>git push -u origin main</b> 
</code></pre>

#### Tag the commit with the Version and Rlease

Tag the commit:
<pre class=console><code>$ <b>git tag 1.2-1</b> 
</code></pre>

And push it to the central repository:
<pre class=console><code>$ <b>git push --tags</b> 
</code></pre>

Note that tags can be listed with:
<pre class=console><code>$ <b>git tag</b> 
1.1-1
1.1-2
</code></pre>

And a view of the logs of the repository will show our tagged version/release.
In the example below, note that the release 2 of version 1.1 has just been
committed/tagged and is the same as the current HEAD.
<pre class=console><code>$ <b>git log --oneline</b> 
git log --oneline
20645b2 (HEAD -> main, tag: 1.1-2) Version 1.1 Release 2
4f7a5ad (origin/main) README
059509e (tag: 1.1-1) Version 1.1 Release 1
e524994 README updates
3979962 README updates
70a2ec2 Moved libraries to pkgpyexec
5914994 Re-arranged
a6c822d Added verify_only
9924dbf Jo's file added to list of modules
cf323fe Made emrun relocatable
97296b2 First collection of files
a254d09 First commit
</code></pre>


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

