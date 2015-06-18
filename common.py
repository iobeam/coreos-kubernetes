#!/usr/bin/env python
#
# Common functionality for generating and merging yaml config files
# and jinja2 templates.
#
from jinja2 import contextfunction, contextfilter, Template, Environment, FileSystemLoader
import sys
import os
import yaml
import re
import urllib2
import json
import inspect

def script_path(subdir):
    if not subdir.startswith('/'):
        subdir = "/" + subdir
    return os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])) + subdir

@contextfunction
def getdict(ctx, name):
    return ctx.get(name)

# Custom jinja2 filter method
def regex_replace(s, find, replace):
    """A non-optimal implementation of a regex filter"""
    return re.sub(find, replace, s)

def jinja2_env(path):
    env = Environment(loader=FileSystemLoader(path))
    env.filters['regex_replace'] = regex_replace
    env.globals['getdict'] = getdict
    return env

## define custom tag handler
def join(loader, node):
    seq = loader.construct_sequence(node)
    return ''.join([str(i) for i in seq])

## register the tag handler
yaml.add_constructor('!join', join)

# Reads yaml  files, first passing them through jinja2
def read_yaml(env, file, params):
    template = env.get_template(file)
    y = yaml.load(template.render(params).encode('utf-8'))

    if not y:
        return {}
    return y

def read_config(cfg_file):
    """
    Reads a simple key=value-style config file
    """
    reg = re.compile('(?P<name>\w+)(\=(?P<value>.+))*')
    conf = {}
    with open(cfg_file) as f:
        for line in f:
            m = reg.match(line)
            if m:
                name = m.group('name')
                value = ''
                
                if m.group('value'):
                    value = m.group('value')
                    conf[name] = value
    return conf
    
def read_global_config():
    return read_config(script_path("global.conf"))
                       
def deepupdate(original, update):
    """
    Recursively update a dict.
    Subdict's won't be overwritten but also updated.
    """
    for key, value in original.iteritems():
        if not key in update:
            update[key] = value
        elif isinstance(value, dict):
            deepupdate(value, update[key])

    return update

def render_template(env, name, dest, params):

    if not dest.endswith("/"):
        dest += "/"
        
    cc = env.get_template(name)
    outfile = dest + name[:-3]
    path = os.path.dirname(outfile)

    if not os.path.exists(path):
        os.makedirs(path)
        
    with open(outfile, 'w+') as f:
        f.write(cc.render(params).encode('utf8'))
        f.write('\n')
    
