#!/usr/bin/python3

import json

with open("unmanaged.json", "r") as read_file:
    objects = json.load(read_file)

for object in objects["data"]:
#    print(object["Properties"])

    if object["Target Type"] == 'cluster':

        d = {k: v for k, v in (item.split(":") for item in object["Properties"].split(";"))}

        for key, value in d.items():
            print(key + ' = ' + value)
            if value.isdigit():
                exec(key + ' = ' + 'int(' +  value + ')')
            else:
                exec(key + ' = ' + '"' + value + '"')

        print('Oracle Home is ' + OracleHome)
        print('scanPort = ' + str(scanPort))

    if object["Target Type"] == 'has':
        for key, value in {k: v for k, v in (item.split(":") for item in object["Properties"].split(";"))}.items():
            print(key + ' = ' + value)
            if value.isdigit():
                exec(key + ' = ' + 'int(' +  value + ')')
            else:
                exec(key + ' = ' + '"' + value + '"')

        print('Oracle Home is ' + OracleHome)
        print('scanPort = ' + str(scanPort))
