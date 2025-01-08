# Python Packages

## creds

This is an interface to the gnome-keyring.

The `gnome-keyring-daemon` is a service that stores your passwords and secrets. It is normally started automatically when a user logs into a desktop session.

The `gnome-keyring-daemon` implements the DBus Secret Service API, and you can use tools like seahorse or secret-tool to interact with it.

 We can use python keyring which is available as an install from EPEL to interact with the gnome-keyring:

```
sudo dnf install python3-keyring
```

The python keyring lib contains implementations for several backends. The library will attempt to automatically choose the most suitable backend for the current environment. Users may also specify the preferred keyring in a config file or by calling the set_keyring() function. 

<pre class=console><code>$ <b>keyring --list-backends</b>
keyring.backends.SecretService.Keyring (priority: 5)
keyring.backends.chainer.ChainerBackend (priority: 10)
keyring.backends.kwallet.DBusKeyring (priority: 4.9)
keyring.backends.fail.Keyring (priority: 0)
keyring.backends.libsecret.Keyring (priority: 4.8)
</code></pre>


### Examples
Create a password for a user:

```Python
# put.py
import keyring
import os

EMCLI_USERNAME_KEY = os.getenv('EMCLI_USERNAME_KEY')
service_id = 'emcli'
username = 'sysman'
password = 'MyOhMy!'

keyring.set_password(service_id, username, password)
keyring.set_password(service_id, EMCLI_USERNAME_KEY, username)
```

Retrieve username and password:

```Python
# get.py
import keyring
import os

EMCLI_USERNAME_KEY = os.getenv('EMCLI_USERNAME_KEY')
service_id = 'emcli'

username = keyring.get_password(service_id, EMCLI_USERNAME_KEY)
password = keyring.get_password(service_id, username)

print('Username: ' + username)
print('Password: ' + password)
```

## Headless Sessions
The opening of the keyring is automatic from the Gnome desktop. However, we should be able to do this via an sshd login.

### Ordinary Login
First we show a standalone example assuming a login session not from desktop; we shall only have the (current) shell running:

<pre class=console><code>$ <b>pgrep -flu oracle -t `expr \`tty\` : '/dev/\(.*\)'`</b>
21554 bash
</code></pre>

We shall need to start a dbus session:
<pre class=console><code>$ <b>export EMCLI_USERNAME_KEY=`cat /export/home/oracle/.config/emcli/username.key`</b>
$ <b>dbus-run-session -- sh</b>
</code></pre>

 Unlock the keyring directly (note that we do not want a trailing newline from `echo`):
<pre class=console><code>$ <b>echo -n 'mylogin-password' | gnome-keyring-daemon --unlock</b>
GNOME_KEYRING_CONTROL=/export/home/oracle/.cache/keyring-X5IJY2
SSH_AUTH_SOCK=/export/home/oracle/.cache/keyring-X5IJY2/ssh
</code></pre>


We can then retrieve the username and password
<pre class=console><code>$ <b>python -m get</b>
Username: sysman
Password: Nadi7932
</code></pre>

### SSH
In the sshd configuration file for PAM ensure that the entries for pam_gnome_keyring.so are present for the auth,  password and session service types as follows:

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

When we login:

<pre class=console><code>$ <b>pgrep -flu oracle</b>
13580 systemd
13585 (sd-pam)
<i>13615</i> gnome-keyring-d
13619 sshd
13624 bash
</code></pre>

You will see a a `gnome-keyring-daemon` login session has been started by the systemd session associated with this account:
<pre class=console><code>$ <b>ps -wwwfp </b><i>13615</i>
UID          PID    PPID  C STIME TTY          TIME CMD
oracle     <i>13615</i>       1  0 22:05 ?        00:00:00 /usr/bin/gnome-keyring-daemon --daemonize --login
</code></pre>

We can then retrieve our password:
<pre class=console><code>$ <b>python -m get</b>
Username: sysman
Password: Nadi7932
</code></pre>

After running the keyring operation we can see an extra `gnome-keyring-daemon`:
<pre class=console><code>$ <b>pgrep -flu oracle</b>
pgrep -flu oracle
13580 systemd
13585 (sd-pam)
13615 gnome-keyring-d
13619 sshd
13624 bash
13714 dbus-broker-lau
13715 dbus-broker
<i>13718</i> gnome-keyring-d
</code></pre>

And that the open keyring is now initialised (started) for use:
<pre class=console><code>$ <b>ps -wwwfp </b><i>13718</i>
UID          PID    PPID  C STIME TTY          TIME CMD
oracle     <i>13718</i>   13580  0 22:06 ?        00:00:00 /usr/bin/gnome-keyring-daemon --start --foreground --components=secrets
</code></pre>

NB to allow graphical interaction:
dbus-update-activation-environment DISPLAY XAUTHORITY 
