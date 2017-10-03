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

nodes = []
master_nodes = []
namespace = "default"
kube_cfg =  os.path.join(os.environ["HOME"], '.kube/config')
cli = client.CoreV1Api()
#cli = client.OapiApi()
config.load_kube_config()

def help():
    print "Usage: monkey --config <path-to-config-file>"
    print "              --kube_config <path-to-kube-config>"

def check_count(before_count, after_count):
    if before_pods == after_pods:
        status = False
    else:
        status = True
        print "looks like the pod has not been rescheduled, test failed"
    return status

###########  check the pod status, count only the pods which are ready########33
    
def node_pod_count(node, label):
    pods = []
    if label == deleted:
        cmd = "oadm manage-node %s --list-pods" %(node)
    else:
        cmd = "oc get pods --all-namespaces"
    with open("/tmp/pods") as pods_file:
        subprocess.Popen(pods_cmd, shell=True, stdout=pods_file).communicate()[0]
        get_pods = pods_file.readlines()[1:]
        for pod in get_pods:
            if pod is None:
                pass
            else:
                pods.append(line.split(' ')[0])
    pod_count = len(pods)
    pods_file.close()
    return pod_count

def pod_count(namespace):
    pods = []
    config.load_kube_config("%s") %(kube_cfg)
    pods_list = cli.list_pod_for_all_namespaces(namespace, watch=False)
    for pod in pods_list.items:
        pods.append(pod.status.pod_ip)
    pod_count = len(pods)
    return pod_count

def check_master(picked_node):
    ret = cli.list_node(pretty=True, label_selector="type=master")
    for data in ret.items:
        master_nodes.append(data.metadata.name)
    if picked_node in master_nodes:
        random_node = get_random_node()
        check_master(random_node)
    return random_node

def get_random_node(label):
    ret = cli.list_node(pretty=True, label_selector=label)
    for data in ret.items:
        nodes.append(data.metadata.name)
    # pick random node to kill
    random_node = random.choice(nodes)
    return random_node

def monkey(label):
    # leave master node out
    # pick random node to kill
    random_node = get_random_node(label)
    random_node = check_master(random_node)
    # get pod count on the node before deleting the node
    before_pods = node_pod_count(random_node, label)
    print "There are %s pods running on the %s node which is going to be deleted" %(before_pods, random_node)
    # count number of pods before deleting the node
    pod_count_before = pod_count(project_name, kube_cfg)
    # delete a node
    cli.delete_node(random_node)
    #check if the node is taken out
    if random_node in nodes:
        print "something went wrong, node didn't get deleted"
    # pod count after deleting the node
    pod_count_after = pod_count(project_name, kube_cfg)
    sleep_counter = 0
    # check if the pods have been rescheduled
    while True:
        print "checking if the pods have been rescheduled"
        time.sleep(60)
        status = check_count(before_pods, pod_count_after)
        if status:
            print "Test passed, pods have been been rescheduled"
            break
        sleep_counter = int(sleep_counter)+60
        if int(sleep_counter) > 900:
            print "Test failed, looks like pods haven't been rescheduled after waiting for 900 seconds"
            sys.exit(1)

def main(cfg, kube_cfg):
    #parse config
    if os.path.isfile(cfg):
        config = ConfigParser.ConfigParser()
        config.read(cfg)
        namespace = config.get('projects','name')
        label = config.get('projects', 'label')
        if label is None:
            monkey()
        else:
            monkey(label)
        gopath = config.get('set-env','gopath')
    else:
        help()
        sys.exit(1)

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", dest="cfg", help="path to the config")
    parser.add_option("--kc", "--kube_config", dest="kube_cfg", help="path to kube_config")
    (options, args) = parser.parse_args()
    if options.kube_cfg is None:
        print "The user haven't specified the kube config path, using the default config file in /home/.kube/"
    if (options.cfg is None):
        help()
        sys.exit(1)
    else:
        main(options.cfg, kube_cfg )
