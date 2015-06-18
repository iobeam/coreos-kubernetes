#!/usr/bin/env python

import common, os, sys, random, base64, urllib2, argparse

parser = argparse.ArgumentParser(description="Generate cloud configs for Vagrant of AWS")
parser.add_argument('-t', default='vagrant', choices=[ 'vagrant', 'aws' ], help='The target environment', metavar="TARGET")

# Replicates behavior of how Kubernetes config scripts generate
# tokens:
# dd if=/dev/urandom bs=128 count=1 2>/dev/null | base64 | tr -d '=+/' | dd bs=32 count=1 2>/dev/null
def generate_kubernetes_system_service_token(size):
    arr = bytearray(random.getrandbits(8) for i in xrange(128))
    return base64.b64encode(arr).translate(None, "=+/")[:size]
    
def get_etcd_discovery_url(size):
    try:
        rsp = urllib2.urlopen("https://discovery.etcd.io/new?size=" + str(size), None, 1)
        return rsp.read()
    except IOError as e:
        print "Could not get etcd discovery URL."
    return None

def add_authorized_keys_dict(params):
    authorized_keys = []
    
    for user in params['users']:
        if 'ssh-authorized-keys' in user:
            for key in user['ssh-authorized-keys']:
                authorized_keys.append(key)

    params['ssh_authorized_keys'] = authorized_keys

def generate_cloud_configs(target, override_params={}):
    
    conf_env = common.jinja2_env(common.script_path('/'))

    # Patch jinja2 with our custom filter
    conf_env.filters['kube_token'] = generate_kubernetes_system_service_token

    # Number of nodes to reach concensus in cluster:
    etcd_size = 1

    if target == "aws":
        etcd_size = 3

    cloud_config_params = common.read_global_config()
    cloud_config_params['groups'] = {}
    defaults = common.read_yaml(conf_env, 'defaults.yaml', cloud_config_params)
    add_authorized_keys_dict(defaults)

    p = common.read_yaml(conf_env, target + '.yaml', cloud_config_params)
    url = get_etcd_discovery_url(etcd_size)

    if not url:
        return None
    
    p['etcd_discovery_url'] = url
    params = common.deepupdate(dict(defaults.items()), p)
    params = common.deepupdate(params, override_params)
    
    env = common.jinja2_env(common.script_path('/templates'))
    
    common.render_template(env, "etcd.yaml.j2", "/tmp", params)
    common.render_template(env, "master.yaml.j2", "/tmp", params)
    common.render_template(env, "node.yaml.j2", "/tmp", params)
    
    return params
    
def main(argv):
    args = parser.parse_args()    
    print "target is", args.t
    
    if not generate_cloud_configs(args.t, {}):
        sys.exit(-1)

    sys.exit(0)
    
if __name__ == "__main__":
    main(sys.argv)

