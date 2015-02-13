__author__ = 'dbaskette'

import argparse
import os
import shutil

import vagrant
from pysphere import VIServer
from pysphere import VIProperty


def getDatastores(clusterPath):
    with open("./Vagrantfile.master", "r") as vagrantfile:
        for line in vagrantfile:
            if "vsphere.host" in line:
                vsphereIP = (line.split("=")[1]).lstrip(" ").replace("'", "").rstrip()
            if "vsphere.user" in line:
                vsphereUser = (line.split("=")[1]).lstrip(" ").replace("'", "").rstrip()
            if "vsphere.password" in line:
                vspherePassword = (line.split("=")[1]).lstrip(" ").replace("'", "").rstrip()
    server = VIServer()
    server.connect(vsphereIP, vsphereUser, vspherePassword)

    datastores = []
    for datastore in server.get_datastores():
        props = VIProperty(server, datastore)
        if props.host and props.summary.accessible == True:
            datastores.append(props.info.name)
    return datastores



def cliParse():
    VALID_ACTION = ["create","delete"]
    parser = argparse.ArgumentParser(description='Pivotal Lab Builder')
    subparsers = parser.add_subparsers(help='sub-command help', dest="subparser_name")
    parser_create = subparsers.add_parser("create", help="Create a Cluster")
    parser_delete = subparsers.add_parser("delete", help="Delete a Cluster")
    parser_create.add_argument("--clustername", dest='clustername', action="store",help="Name of Cluster to be Created",required=True)
    parser_create.add_argument("--nodes", dest='nodes', default=1, action="store", help="Number of Nodes to be Created",required=True)
    parser_delete.add_argument("--clustername", dest='clustername', action="store",help="Name of Cluster to be Deleted",required=True)
    args = parser.parse_args()
    clusterDictionary = {}
    if (args.subparser_name == "create"):
        clusterDictionary["clustername"] = args.clustername
        clusterDictionary["nodes"] = args.nodes
        create(clusterDictionary)
    elif (args.subparser_name == "delete"):
        clusterDictionary["clustername"] = args.clustername
        delete(clusterDictionary)


def create(clusterDictionary):
    if not os.path.exists(clusterDictionary["clustername"]):
        os.makedirs(clusterDictionary["clustername"])
    clusterPath = "./"+clusterDictionary["clustername"]
    shutil.copy("dummy.box",clusterPath)
    shutil.copy("metadata.json",clusterPath)
    shutil.copy("gpssh-exkeys",clusterPath)

    datastores = getDatastores(clusterPath)

    with open (clusterPath+"/Vagrantfile","w") as vagrantfile:
        vagrantfile.write("DATASTORES=" + str(datastores))
        with open("./Vagrantfile.master") as master:
            for line in master:
                if "$CLUSTERNAME" in line:
                    vagrantfile.write(line.replace("$CLUSTERNAME","'"+clusterDictionary["clustername"]+"'"))
                elif "$CLUSTERNODES" in line:
                     vagrantfile.write(line.replace("$CLUSTERNODES",clusterDictionary["nodes"]))
                else:
                     vagrantfile.write(line)

    os.chdir(clusterPath)
    v = vagrant.Vagrant(quiet_stdout=False)
    v.up(provider="vsphere")
    sshConfig = v.ssh_config()
    config = sshConfig.split("\n")
    nodes = []
    nodeInfo = {}

    for line in config:
        line = line.lstrip(" ")
        if "Host " in line:
            nodeInfo["hostname"]= line.split(" ")[1]
        elif "HostName" in line:
            nodeInfo["ipAddress"]= line.split(" ")[1]
            nodes.append(nodeInfo)
            nodeInfo={}


#    sharekeys(nodes,clusterDictionary["clustername"])


    print "******************************************"
    print "Cluster: "+clusterDictionary["clustername"]+" has been created"
    print "******************************************"
    for node in nodes:
        print node



#def sharekeys(nodes,clustername):
 #   print "sharekeys"


def delete(clusterDictionary):


    clusterPath = "./"+clusterDictionary["clustername"]
    os.chdir(clusterPath)

    v = vagrant.Vagrant(quiet_stdout=False)
    v.destroy()
    os.chdir("../")

    shutil.rmtree(clusterPath)
    print "******************************************"
    print "Cluster: "+clusterDictionary["clustername"]+" has been deleted"
    print "******************************************"



if __name__ == '__main__':
    cliParse()