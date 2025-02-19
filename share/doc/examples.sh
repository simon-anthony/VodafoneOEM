#!/usr/bin/sh -

echo "++++++ >>> Clusters ++++++"
jq '.[]|.[]|select(."Target Type" | test("^cluster$"; "ig"))' < unmanaged.json

echo "++++++ >>> RAC Databases ++++++"
jq '.[]|.[]|select(."Target Type" | test("rac_database"; "ig"))' < unmanaged.json

echo "++++++ >>> Oracle Databases ++++++"
jq '.[]|.[]|select(."Target Name" | test("vdf.*.example.com"; "ig"))|select(."Target Type" | test("oracle_database"; "ig"))' < unmanaged.json

echo "++++++ >>> HA Nodes ++++++"
jq '.[]|.[]|select(."Target Type" | test("ha"; "ig"))' < unmanaged.json

echo "++++++ >>> Listeners ++++++"
jq '.[]|.[]|select(."Properties" | test("LsnrName:LISTENER;"; "ig"))' < unmanaged.json

echo "++++++ >>> SCAN Listeners ++++++"
jq '.[]|.[]|select(."Properties" | test("LsnrName:LISTENER_SCAN"; "ig"))' < unmanaged.json

echo "++++++ >>> DB Oracle Home ++++++"
jq '.[]|.[]|select(."Target Type" | test("oracle_home"; "ig"))|select(."Target Name" | test("^OraDB"; "ig"))' < unmanaged.json

echo "++++++ >>> GI Oracle Home ++++++"
jq '.[]|.[]|select(."Target Type" | test("oracle_home"; "ig"))|select(."Target Name" | test("^OraGI"; "ig"))' < unmanaged.json

echo "++++++ >>> Other (Agent) Oracle Home ++++++"
jq '.[]|.[]|select(."Target Type" | test("oracle_home"; "ig"))|select(."Target Name" | test("^OraHome"; "ig"))' < unmanaged.json

echo "++++++ >>> Hostnames in Cluster (SCAN) ++++++"
jq -r '[ .[]|.[]|
		select(."Properties" | test("LsnrName:LISTENER_SCAN"; "ig")) |
		."Host Info" | split(";") | to_entries | .[] | select(.key == 0) |
		.value | split(":") |
		to_entries | .[] | select(.key == 1) ] |
	unique_by(.value) | .[] | .value
	' < unmanaged.json

cluster="vdf-cluster"
jq -r '[ .[]|.[]|
		select(."Properties" | test("LsnrName:LISTENER_SCAN"; "ig")) | 
		select(."Target Name" | test("_'$cluster'$"; "ig")) |
		."Host Info" | split(";") | to_entries | .[] | select(.key == 0) |
		.value | split(":") |
		to_entries | .[] | select(.key == 1) ] |
	unique_by(.value) | .[] | .value
	' < unmanaged.json
