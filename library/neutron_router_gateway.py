#!/usr/bin/python
#coding: utf-8 -*-

# (c) 2013, Benno Joy <benno@ansibleworks.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software. If not, see <http://www.gnu.org/licenses/>.

try:
    from neutronclient.neutron import client
    from keystoneauth1.identity import v2
    from keystoneauth1 import session
    from keystoneclient.v2_0 import client as ksclient
except ImportError:
    print("failed=True msg='neutronclient and keystone client are required'")
DOCUMENTATION = '''
---
module: neutron_router_gateway
version_added: "1.2"
short_description: set/unset a gateway interface for the router with the specified external network
description:
   - Creates/Removes a gateway interface from the router, used to associate a external network with a router to route external traffic.
options:
   login_username:
     description:
        - login username to authenticate to keystone
     required: true
     default: admin
   login_password:
     description:
        - Password of login user
     required: true
     default: 'yes'
   login_tenant_name:
     description:
        - The tenant name of the login user
     required: true
     default: 'yes'
   auth_url:
     description:
        - The keystone URL for authentication
     required: false
     default: 'http://127.0.0.1:35358/v2.0/'
   region_name:
     description:
        - Name of the region
     required: false
     default: None
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
   router_name:
     description:
        - Name of the router to which the gateway should be attached.
     required: true
     default: None
   network_name:
     description:
        - Name of the external network which should be attached to the router.
     required: true
     default: None
   enable_snat:
     description:
        - Enable SNAT on traffic using this gateway (may require admin role).
     required: false
     default: true
   fixed_ip:
     description:
        - IP Address for this router's external gateway.
     required: false
requirements: ["neutronclient", "keystoneclient"]
'''

EXAMPLES = '''
# Attach an external network with a router to allow flow of external traffic
- neutron_router_gateway: state=present login_username=admin login_password=admin
                          login_tenant_name=admin router_name=external_router
                          network_name=external_network
'''

_os_keystone = None
def _get_ksclient(module, kwargs):
    try:
        auth = v2.Password(auth_url=kwargs.get('auth_url'),
                           username=kwargs.get('login_username'),
                           password=kwargs.get('login_password'),
                           tenant_name=kwargs.get('login_tenant_name'))
        sess = session.Session(auth=auth, verify=kwargs.get('verify'))

        kclient = ksclient.Client(session=sess)
        nclient = client.Client('2.0', session=sess)
    except Exception as e:
        module.fail_json(msg = "Error authenticating to the keystone: %s" %e.message)
    global _os_keystone
    _os_keystone = kclient
    return nclient


def _get_endpoint(module, ksclient):
    try:
        endpoint = ksclient.service_catalog.url_for(service_type='network', endpoint_type='publicURL')
    except Exception as e:
        module.fail_json(msg = "Error getting endpoint for glance: %s" % e.message)
    return endpoint

def _get_neutron_client(module, kwargs):
    try:
        neutron = _get_ksclient(module, kwargs)
    except Exception as e:
        module.fail_json(msg = " Error in connecting to Neutron: %s " %e.message)
    return neutron

def _get_router(module, neutron):
    kwargs = {
            'name': module.params['router_name'],
    }
    try:
        routers = neutron.list_routers(**kwargs)
    except Exception as e:
        module.fail_json(msg = "Error in getting the router list: %s " % e.message)
    if not routers['routers']:
            return None
    return routers['routers'][0]

def _get_net_id(neutron, module):
    kwargs = {
        'name': module.params['network_name'],
        'router:external': True
    }
    try:
        networks = neutron.list_networks(**kwargs)
    except Exception as e:
        module.fail_json("Error in listing neutron networks: %s" % e.message)
    if not networks['networks']:
        return None
    return networks['networks'][0]['id']

def _add_gateway_router(neutron, module, router_id, network_id):
    if module.params['fixed_ip'] is not None:
        kwargs = {
            'network_id': network_id,
            'enable_snat': module.params['enable_snat'],
            'external_fixed_ips': [{'ip_address': module.params['fixed_ip']}]
        }
    else:
        kwargs = {
            'network_id': network_id,
            'enable_snat': module.params['enable_snat'],
        }

    try:
        neutron.add_gateway_router(router_id, kwargs)
    except Exception as e:
        module.fail_json(msg = "Error in adding gateway to router: %s" % e.message)
    return True

def _remove_gateway_router(neutron, module, router_id):
    try:
        neutron.remove_gateway_router(router_id)
    except Exception as e:
        module.fail_json(msg = "Error in removing gateway to router: %s" % e.message)
    return True

def main():

    module = AnsibleModule(
        argument_spec = dict(
            login_username = dict(default='admin'),
            login_password = dict(required=True),
            login_tenant_name = dict(required='True'),
            auth_url = dict(default='http://127.0.0.1:35358/v2.0/'),
            region_name = dict(default=None),
            router_name = dict(required=True),
            network_name = dict(required=True),
            enable_snat = dict(default=True, type='bool'),
            fixed_ip = dict(required=False),
            state = dict(default='present', choices=['absent', 'present']),
            verify = dict(type='bool', default=False)
        ),
    )

    neutron = _get_neutron_client(module, module.params)
    router = _get_router(module, neutron)

    if not router:
        module.fail_json(msg="failed to get the router id, please check the router name")

    network_id = _get_net_id(neutron, module)
    if not network_id:
        module.fail_json(msg="failed to get the network id, please check the network name and make sure it is external")

    if module.params['state'] == 'present':
        if router.get('external_gateway_info') is None:
            _add_gateway_router(neutron, module, router['id'], network_id)
            module.exit_json(changed=True, updated=False, result="created")
        else:
            if router['external_gateway_info']['network_id'] == network_id \
                    and router['external_gateway_info']['enable_snat'] == module.params['enable_snat']:
                if module.params['fixed_ip'] is not None:
                    if router['external_gateway_info']['external_fixed_ips'][0]['ip_address'] == module.params['fixed_ip']:
                        module.exit_json(changed=False, updated=False, result="success")
                    else:
                        _add_gateway_router(neutron, module, router['id'], network_id)
                        module.exit_json(changed=True, updated=True, result="updated")
                else:
                    module.exit_json(changed=False, updated=False, result="success")
            elif router['external_gateway_info']['network_id'] == network_id:
                _add_gateway_router(neutron, module, router['id'], network_id)
                module.exit_json(changed=True, updated=True, result="updated")
            else:
                _remove_gateway_router(neutron, module, router['id'])
                _add_gateway_router(neutron, module, router['id'], network_id)
                module.exit_json(changed=True, updated=True, result="created")

    if module.params['state'] == 'absent':
        if router.get('external_gateway_info') is None:
            module.exit_json(changed=False, updated=False, result="success")
        else:
            _remove_gateway_router(neutron, module, router['id'])
            module.exit_json(changed=True, updated=False, result="deleted")

# this is magic, see lib/ansible/module.params['common.py
from ansible.module_utils.basic import *
main()
