# Additional Modules - libexec

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
    print(json.dumps(targets.out(), indent=4))

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
