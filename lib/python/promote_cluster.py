from emcli.exception import VerbExecutionError
import sys
from vf import *
import datetime as dt
 
alltargets=False
targetparms=0
today=dt.datetime.now().strftime("%Y%m%d")
 
def helpUsage():
   print 'Usage: promote_discovered_dbs.py [-help]'
   print '[-all] Add all discovered Single Instance DBs'
   print '[-targets <target1:target2:...] Add only targets listed'
   sys.exit()
regions=['dublin', 'milan', 'rating']
oem_urls= { 'dublin': 'https://vg00071de.snc5003.ie1ds014001oci1.oraclevcn.com:7799/em', 'milan': 'https://vg00011de.snc5003.it1ds014001oci1.oraclevcn.com:7799/em', 'rating' : 'https://vg00041de.snc5003.de1ds014001oci1.oraclevcn.com:7803/em'}
 
 
 
for i in range(len(sys.argv)):
   if sys.argv[i] in ("-help"):
      helpUsage()
   elif sys.argv[i] in ("-targets"):
      if i+1 < len(sys.argv):
         targetparms = sys.argv[i+1]
      else:
         print 'Usage: promote_discovered_dbs.py [-help]'
         print '[-all] Add all discovered Single Instance DBs'
         print '[-targets <target1:target2:...] Add only targets listed'
         sys.exit()
   elif sys.argv[i] in ("-reg"):
      if i+1 < len(sys.argv):
         region = sys.argv[i+1]
   elif sys.argv[i] in ("-all"):
           alltargets = True
regiondir="/opt/oracle/report/"  + region + "/"
cluster_file=regiondir + region + "_hosts_by_cluster_" + today +".csv"
print("Info: adding clusters")
# Make sure user did not specify target list and all targets.
if alltargets<>0 and targetparms <>0:
    print 'Cannot specify target list and all switch'
    print 'Usage: promote_discovered_dbs.py -reg <region> -username <username> -password <password> -monitor_pw <password>'
    print '[-all] Add all discovered SI Databses'
    print '[-targets <target1:target2:...] Add only list targets'
    print '[-help]'
    sys.exit()
 
#Setup EMCLI environment
set_url(region)
 
#Connect as dba_build
conn_vf_dba_build()
 
if targetparms <> 0:
   targetparms = targetparms.replace(":",":oracle_database;")+":oracle_database"
   target_array = get_targets(unmanaged=True,properties=True,targets=targetparms).out()['data']
elif alltargets:
   target_array = get_targets(targets="cluster",unmanaged=True,properties=True ).out()['data']
else:
   print 'Missing required arguments (-targets or -all)'
   helpUsage()
 
if len(target_array) > 0:
   for target in target_array:
      print 'name=' + target['Target Name']
      properties=target['Properties']
      for host in str.split(target['Host Info'],";"):
         if host.split(":")[0] == "host":
            print 'Host=' + host.split(":")[1]
            myhost=host.split(":")[1]
      print 'Properties=' + properties,
      print 'name=' + target['Target Name'] + ',host=' + host.split(":")[1] + ',properties=' + target['Properties']
      with open(cluster_file) as fh:
         for line in fh:
            if myhost in line:
               my_list=line.split(",")
               while ("" in my_list):
                  my_list.remove("")
               s=':host;'
               myinstances=s.join(my_list).strip().rstrip(';')
               #print 'instances=' + myinstances[:-1]
               #print 'instances=' + myinstances.rstrip(';')
               print 'instances=' + myinstances
 
      try:
         #res1 = add_target(type='cluster',name=target['Target Name'],host=host.split(":")[1],properties=target['Properties'])
         res1 = add_target(name=target['Target Name'],type='cluster',host=myhost,monitor_mode='1',properties=target['Properties'],instances=myinstances)
         print 'Succeeded'
      except VerbExecutionError, e:
         print 'Failed'
         print e.error()
         print 'Exit code:'+str(e.exit_code())
else:
   print 'INFO: There are no targets to be promoted. Please verify the targets in Enterprise Manager webpages.'


