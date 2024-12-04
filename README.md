# OEM Deployment Tools 

Tools to support OEM activities.


## Getting Started


### Prerequisites

#### Linux Packages
Additional packages may be required.

They will be automatically installed if the repositories are available.
Otherwise download these packages and install them beforehand.

## Installing from Packages

To download the latest RPM packages and review release notes, see the [VODAFONEoem releases](https://github.com/simon-anthony/vodafone/releases) page.

Install the package with the usual RPM based tools: `rpm`, `yum` or `dnf`.

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. 


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

## Usage

Details to follow.

### Examples

We use a wrapper to invoke programs from our catalogue. To list the modules
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

<pre><code>
user=sysman
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
Set `%_topdir` in the file `$HOME/.rpmmacros`

<pre><code>topdir=`eval echo \`sed -n '
    /^%_topdir/ {
        s;%_topdir[     ]*;;
        s;%{getenv:HOME};$HOME;
        p
    }' ~/.rpmmacros\``

echo topdir is $topdir
</code></pre>

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


## Authors

* **Simon Anthony** - *Initial work* - * [Simon Anthony](https://github.com/simon-anthony)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

