# Kubernetes on CoreOS using Fleet #

Generate CoreOS cloud configs that allow installing Kubernetes via
Fleet on Vagrant or AWS. Kubernetes is configured with secure
connections and token authentication.

On AWS, these scripts target a CoreOS cluster consisting of a three
node *etcd*-cluster, where one etcd node is the Kubernetes master. Any
number of Kubernetes nodes can specified, but these do not run etcd
themselves.

Configuration overview:

- `global.conf`: global configuration that applies to all targets
(AWS, Vagrant).
- `defaults.yaml` default cloud-config configuration that applies to
all targets.
- `vagrant.yaml` configuration specific to Vagrant (overrides values
in `defaults.yaml`).
- `aws.yaml` configuration specific to AWS (overrides values
in `defaults.yaml`).

## Run on Vagrant ##

You can run these cloud-configs with Vagrant. Simply do:

    vagrant up

and this will launch one master and two nodes where only the master
runs etcd. Set a different number of Kubernetes nodes via the
`NUM_NODES` environment variable, e.g.,:

    NUM_NODES=3 vagrant up

## Generate Cloud Configs for AWS ##

On AWS, this cloud config targets a cluster of two etcd-running
instances, one Kubernetes master (also running etcd), and any number
of Kubernetes nodes (matching a CoreOS production cluster). If needed,
edit the settings in the above configuration files, if needed
(specifically, you might want to add a user and ssh keys to
`defaults.yaml`).

To generate the cloud-config for a target, run:

    ./make_cloud_config.py -t aws

If the `-t` option is omitted the target defaults to Vagrant. The
actual cloud-configs ends up in `/tmp/etcd.yaml`, `/tmp/master.yaml`
and `/tmp/node.yaml`.

Now launch two etcd instances, and one master. Note the private IP
addresses of those instances and manually update the `etcd_servers`
for Fleet and `etcd_endpoints` for Flannel in the `node.yaml` cloud
config. Then launch any number of nodes using the updated cloud
config. Note that the master and the nodes need to be associated with
a AWS security role with full EC2 access policy (or use the policy
files from the official Kubernetes project).

## Installing and Running Kubernetes ##

When a CoreOS cluster is running, either on Vagrant or AWS, install
Kubernetes on the CoreOS cluster using Fleet:

    ./kube-up.sh [ MASTER_IP ]

On Vagrant, the `MASTER_IP` can be omitted. On AWS, you obviously need
access to Kubernetes on all relevant ports (e.g, 2379, 8080),
typically from another machine in the same AWS VPC.

After a short while, you should be able to query the Kubernets master
(e.g, on Vagrant):

    ./kubectl --server=http://172.17.8.101:8080 get pods
