# Modules - libexec

## vf_deploy_agent

### Usage
```console
usage: deploy_agent [-h] [-o OMS | -r REGION] -n NODE [-u USERNAME]
                    [-i IMAGE_NAME] [-B INSTALLATION_BASE_DIRECTORY]
                    [-I INSTANCE_DIRECTORY] [-C CREDENTIAL_NAME]
                    [-O CREDENTIAL_OWNER] [-D DOMAIN] [-w] [-x] -l STATUS -c
                    CENTER -d DEPT -b TEXT
                    HOST [HOST ...]

Add agent to hosts with specified proprties

positional arguments:
  HOST                  list of host(s)

optional arguments:
  -h, --help            show this help message and exit
  -o OMS, --oms OMS     URL for Enterprise Manager Console
  -r REGION, --region REGION
                        REGION: dublin, milan, rating, local
  -n NODE, --node NODE  NODE: db, compute, local
  -u USERNAME, --username USERNAME
                        OMS user, overides that found in
                        /usr/local/share/vodafoneoem/node.ini
  -i IMAGE_NAME, --image_name IMAGE_NAME
                        agent gold image name, default 'agent_gold_image'
  -B INSTALLATION_BASE_DIRECTORY, --installation_base_directory INSTALLATION_BASE_DIRECTORY
                        installation base directory
  -I INSTANCE_DIRECTORY, --instance_directory INSTANCE_DIRECTORY
                        instance directory
  -C CREDENTIAL_NAME, --credential_name CREDENTIAL_NAME
                        credential name to login to host(s)
  -O CREDENTIAL_OWNER, --credential_owner CREDENTIAL_OWNER
                        owner credential name to login to host(s)
  -D DOMAIN, --domain DOMAIN
                        default domain name if missing from host
  -w, --wait            wait for completion
  -x, --exists_check    check if targets are already registered in OEM and
                        quit if found
  -l STATUS, --lifecycle_status STATUS
                        STATUS: Development, MissionCritical, Production,
                        Stage, nonprod
  -c CENTER, --cost_center CENTER, --bs_company CENTER
                        CENTER: Vodafone Albania, Vodafone Czech Republic,
                        Vodafone Germany, Vodafone Group, Vodafone Group
                        Service Gmbh, Vodafone Group Technology Security,
                        Vodafone Ireland, Vodafone Roaming Services, Vodafone
                        United Kingdom
  -d DEPT, --department DEPT, --support_group DEPT
                        DEPT: VC DCOPS Compute Linux OPS-INFRA SVR, VC DCOPS
                        Compute Linux-TSSI OPS-INFRA SVR, VC DCOPS Database
                        Oracle North OPS-INFRA DB, VC DCOPS Database Oracle
                        North-TSSC OPS-INFRA DB, VC DCOPS Database Oracle
                        South-TSSC OPS-INFRA DB
  -b TEXT, --line_of_business TEXT, --bs_service TEXT
                        TEXT is not constrained at present

The .ini files found in /usr/local/share/vodafoneoem contain values for NODE
(node.ini), REGION (region.ini) and STATUS, CENTER, DEPT (properties.ini).
Values for STATUS, CENTER and DEPT must be quoted if they contain spaces
```

### Example
```bash
emrun -s oms -- vf_deploy_agent -x -w -D example.com \
	-r local -n local -l Development \
	-c 'Vodafone Germany' \
	-d 'VC DCOPS Compute Linux OPS-INFRA SVR' \
	-b 'Simon Test' vdf1 vdf2
```

## vf_promote_cluster
To promote discovered, unmanaged cluster database targets the following
method is used. This is based on notes:

1911671.1	_How to add Cluster ASM Target_

1908635.1	_How to Discover the Cluster and Cluster Database (RAC) Target_

The process (1911671.1) is:

<style type="text/css">
    ol ol ol { list-style-type: lower-roman; }
</style>

1) Add the Cluster Target (1908635.1)

	In order to discover the cluster database (rac_database) target it is necessary to:

	a) An agent installed on all nodes of the cluster (1360183.1)

	b) It is also necessary to firstly discover (add) the 'cluster' target.

	The steps here are:

			i) Add the Cluster Target (this will also add the Oracle High Availability Service Target

			add_target type='cluster'
 
			ii) Add the Database Instance Targets (first node)

			add_target type='oracle_database'
 
			iii) Add the Database Instance Targets (remaining nodes)

			add_target type='oracle_database'

			iv) Add the Cluster Database (RAC) Target

			add_target type='rac_database'

2) Add the ASM Instance Targets

3) Add the Cluster ASM

> [!NOTE]
> The API is not able to retrieve information about unmanaged targets.

First we retrieve (JSON) information about the cluster (note that only one
hosts is ever listed in "Host Info" even though there will be multiple nodes
in a cluster):
```python
get_targets(targets = '<cluster_name>:cluster', unmanaged = True, properties = True)
```
<pre class=console><code>{
    "data": [
        {
            "Host Info": "host:vdf2.example.com;timezone_region:Europe/London",
            "Target Type": "cluster",
            "Properties": "OracleHome:/opt/oracle/product/19c/grid;isLongPollConfigured:NO;eonsPort:2016;<b>scanName</b>:<i>vdf-cluster-scan.vdf-cluster.grid.example.com</i>;scanPort:1521",
            "Associations": "",
            "Target Name": "vdf-cluster"
        }
    ]
}
</code></pre>

Note that only one hosts is ever listed in "Host Info" even though there will be
multiple nodes in a cluster. The challenge is to find which nodes.

If we retrieve all unamanged targets we can observe that we can piece together
which nodes are in the cluster from the SCAN information. Subsequently we can
filter these targets based on the target type (<samp>oracle_listener</samp>) and standard naming pattern for
SCAN listeners (we also check that <b><samp>Machine</samp></b> in the SCAN properties matches the <b><samp>scanName</samp></b>
in the cluster properties).

```python
get_targets(targets = 'LISTENER_SCAN%_<cluster_name>:oracle_listener', unmanaged = True, properties = True)
```
<pre class=console><code>{
    "data": [
        ...
        {
            "Host Info": "host:vdf2.example.com;timezone_region:Europe/London",
            "Target Type": "oracle_listener",
            "Properties": "Protocol:TCP;LsnrName:LISTENER_SCAN1;ListenerOraDir:/opt/oracle/product/19c/grid/network/admin;<b>Machine</b>:<i>vdf-cluster-scan.vdf-cluster.grid.example.com</i>;OracleHome:/opt/oracle/product/19c/grid;Port:1521",
            "Associations": "",
            "Target Name": "LISTENER_SCAN1_vdf-cluster"
        },
        {
            "Host Info": "host:vdf1.example.com;timezone_region:Europe/London",
            "Target Type": "oracle_listener",
            "Properties": "Protocol:TCP;LsnrName:LISTENER_SCAN2;ListenerOraDir:/opt/oracle/product/19c/grid/network/admin;<b>Machine</b>:<i>vdf-cluster-scan.vdf-cluster.grid.example.com</i>;OracleHome:/opt/oracle/product/19c/grid;Port:1521",
            "Associations": "",
            "Target Name": "LISTENER_SCAN2_vdf-cluster"
        },
        {
            "Host Info": "host:vdf1.example.com;timezone_region:Europe/London",
            "Target Type": "oracle_listener",
            "Properties": "Protocol:TCP;LsnrName:LISTENER_SCAN3;ListenerOraDir:/opt/oracle/product/19c/grid/network/admin;<b>Machine</b>:<i>vdf-cluster-scan.vdf-cluster.grid.example.com</i>;OracleHome:/opt/oracle/product/19c/grid;Port:1521",
            "Associations": "",
            "Target Name": "LISTENER_SCAN3_vdf-cluster"
        },
        ...
    ]
}
</code></pre>

## Local Modules Called by EMCLI

Note that the following can be used as substitution variables in the
scripts:

```m4
@BASEDIR@
@SBINDIR@
@BINDIR@
@LIBDIR@
@DATADIR@
@PKGDATADIR@
@LIBEXECDIR@
@DATADIR@
@SYSCONFDIR@
@LOCALSTATEDIR@
@PACKAGE@
@PREFIX@
@PYTHON_VERSION@
```

## Programming Notes

### Response Returned by Verbs
Every EM CLI verb invocation returns a Response object. The Response object is part of EM
CLI, and has the functions listed in the table below:

| Function      | Description |
|---------------|-------------|
| `out()`       | Provides the verb execution output. The output can be text, or the JSON.isJson() method on the Response object can be used to determine whether the output is JSON. Refer to the section "JSON Processing" for more details. |
| `error()`     | Provides the error text (if any) of the verb execution if there are any errors or exceptions during verb execution. Refer to the section "Error and Exception Handling" for more details. |
| `exit_code()` | Provides the exit code of the verb execution. The exit code is zero for a successful execution and non-zero otherwise. Refer to the section "Error and Exception Handling" for more details. |
| `isJson()`    | Provides details about the type of output. It returns True if response.out() can be parsed into a JSON object. |

#### JSON Processing
If a verb response is JSON, it can be interactively iterated and accessed. You can use
`response.isJson()` to check whether the verb output is JSON. If the verb output is JSON,
`response.out()['data']` provides the object in the Jython object model.

In the examples below, *submit_add_host()* returns text not JSON. However, verbs such as *get_targets()* return JSON. Whilst not necessary in these examples, the tests for JSON are included nevertheless for illustration:

```python
import re

resp = submit_add_host(
        host_names = host_names,
        platform = platform,
        installation_base_directory = installation_base_directory,
        credential_name = credential_name,
        credential_owner = credential_owner,
        instance_directory = instance_directory,
        wait_for_completion = True,
        image_name = image_name)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

print(resp.out())

if not resp.isJson():
    print('Repsonse is NOT JSON')
    m = re.search(r"^OverAll Status : (?P<status>.+)$", resp.out(), re.MULTILINE)
    if m:
        status = m.group('status')
    else:
        print 'Error: Cannot extract status return'
        sys.exit(1)

print('Info: status is : ' + status)
```

Output:
```console
Session Name : ADD_HOST_SYSMAN_03-Feb-2025_22:21:56_GMT
OverAll Status : Agent Deployment Succeeded

Host              Platform Name  Initialization  Remote Prerequisite  Agent Deployment  Error
vdf1.example.com  Linux x86-64   Succeeded       Succeeded            Succeeded       
vdf2.example.com  Linux x86-64   Succeeded       Succeeded            Succeeded       

Session Name : ADD_HOST_SYSMAN_03-Feb-2025_22:21:56_GMT
OverAll Status : Agent Deployment Succeeded

Host              Platform Name  Initialization  Remote Prerequisite  Agent Deployment  Error
vdf1.example.com  Linux x86-64   Succeeded       Succeeded            Succeeded       
vdf2.example.com  Linux x86-64   Succeeded       Succeeded            Succeeded      

Repsonse is NOT JSON
Info: status is : Agent Deployment Succeeded
```

The following shows the use of JSON:

```python
import json

try:
    resp = get_targets(targets='%:'+target_type)

except emcli.exception.VerbExecutionError, e:
    print e.error()
    exit(1)

if resp.isJson():
    print('Repsonse is JSON')
    print(json.dumps(resp.out(), indent=4))

# refer to elements directly
for target in resp.out()['data']:
    print target['Target Name']
```
Output:

```console
Repsonse is JSON
{
    "data": [
        {
            "Status": "Up",
            "Warning": "1",
            "Status ID": "1",
            "Target Type": "host",
            "Critical": "0",
            "Target Name": "vdf1.example.com"
        },
        {
            "Status": "Up",
            "Warning": "1",
            "Status ID": "1",
            "Target Type": "host",
            "Critical": "0",
            "Target Name": "vdf2.example.com"
        },
		...
    ]	
}
vdf1.example.com
vdf2.example.com
...
```
