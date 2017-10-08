#!/usr/bin/env python

from crontab import CronTab
import sys, os, yaml, time
import optparse
import random
import subprocess
import ConfigParser
import tempfile
import requests
#from openshift import client, config
from kubernetes import client, config
from colorama import init
from colorama import Fore, Back, Style

nodes = []
master_nodes = []
kube_cfg =  os.path.join(os.environ["HOME"], '.kube/config')
config.load_kube_config()
cli = client.CoreV1Api()
body = client.V1DeleteOptions()
#cli = client.OapiApi()
init()

def help():
    print (Fore.GREEN + 'Usage: monkey --config <path-to-config-file>')

def list_nodes(label):
    nodes = []
    ret = cli.list_node(pretty=True, label_selector=label)
    for node in ret.items:
        nodes.append(node.metadata.name)
    return nodes

def check_count(before_count, after_count):
    if before_count == after_count:
        status = True
    else:
        status = False
        print(Fore.RED + 'looks like the pod has not been rescheduled, test failed\n')
    return status

def pod_count():
    pods = []
    pods_list = cli.list_pod_for_all_namespaces(watch=False)
    for pod in pods_list.items:
        pods.append(pod.status.pod_ip)
    count = len(pods)
    return count

def check_master(picked_node):
    ret = cli.list_node(pretty=True, label_selector=master_label)
    for data in ret.items:
        master_nodes.append(data.metadata.name)
    if picked_node in master_nodes:
        picked_node = get_random_node()
        check_master(random_node)
    return picked_node

def get_random_node(label):
    if label == "undefined":
        ret = cli.list_node()
    else:
        ret = cli.list_node(pretty=True, label_selector=label)
    for data in ret.items:
        nodes.append(data.metadata.name)
    # pick random node to kill
    random_node = random.choice(nodes)
    return random_node

def node_pod_count(node):
    cmd = "oadm manage-node %s --list-pods" %(node)
    with open("/tmp/pods","w") as list_pods:
        subprocess.Popen(cmd, shell=True, stdout=list_pods).communicate()[0]
    with open("/tmp/pods","r") as pods_file:
        get_pods = pods_file.readlines()[1:]
    return len(get_pods)

def monkey(label):
    # get list of nodes
    list_nodes(label)
    # leave master node out
    # pick random node to kill
    random_node = get_random_node(label)
    random_node = check_master(random_node)
    # count number of pods before deleting the node
    pod_count_node = node_pod_count(random_node)
    pod_count_before = pod_count()
    print (Fore.YELLOW + 'There are %s pods before deleting the node and %s pods running on the node picked to be deleted from the cluster\n') %(pod_count_before, pod_count_node)
    # delete a node
    print (Fore.GREEN + 'deleting %s\n') %(random_node)
    cli.delete_node(random_node, body)
    #check if the node is taken out
    delete_counter = 0
    while True:
        print (Fore.YELLOW + 'waiting for %s to get deleted\n') %(random_node)
        time.sleep(60)
        if random_node in list_nodes(label):
            delete_counter = delete_counter+60
        else:
            print (Fore.GREEN + '%s deleted\n') %(random_node)
            break
        if delete_counter > 120:
            print (Fore.RED + 'something went wrong, node did not get deleted\n')
            sys.exit(1)
    # pod count after deleting the node
    pod_count_after = pod_count()
    sleep_counter = 0
    # check if the pods have been rescheduled
    while True:
        print (Fore.YELLOW + 'checking if the pods have been rescheduled\n')
        time.sleep(60)
        status = check_count(pod_count_before, pod_count_after)
        if status:
            print (Fore.GREEN 'Test passed, pods have been been rescheduled\n')
            break
        sleep_counter = sleep_counter+60
        if sleep_counter > 900:
            print (Fore.RED + 'Test failed, looks like pods have not been rescheduled after waiting for 900 seconds\n')
            sys.exit(1)

def main(cfg):
    #parse config
    if os.path.isfile(cfg):
        config = ConfigParser.ConfigParser()
        config.read(cfg)
        namespace = config.get('projects','name')
        label = config.get('projects', 'label')
        master_label = config.get('projects', 'master_label')
        if (label is None):
            print (Fore.YELLOW + 'label is not provided, assuming you are okay with deleting any of the available nodes except the master\n')
            label = "undefined"
        monkey(label)
        gopath = config.get('set-env','gopath')
    else:
        help()
        sys.exit(1)

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", dest="cfg", help="path to the config")
    (options, args) = parser.parse_args()
    print (Fore.YELLOW + 'Using the default config file in ~/.kube/config')
    if (options.cfg is None):
        help()
        sys.exit(1)
    else:
        main(options.cfg)
