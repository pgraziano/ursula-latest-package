#!/usr/bin/python
# Copyright 2016, IBM
# Copyright 2016, Jesse Keating <jkeating@j2solutions.net>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

try:
    import shade
    from shade import exc
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_nova_host_agg_host
short_description: Manage OpenStack compute host aggregate host
extends_documentation_fragment: openstack
version_added: "2.1"
author: "Jesse Keating (@iamjkeating)"
description:
   - Add or remove host from an aggregate in OpenStack.
options:
   state:
     description:
        - Indicate desired state of the resource.
     choices: ['present', 'absent']
     required: false
     default: present
   name:
     description:
        - Host aggregate name or ID.
     required: true
   host:
     description:
        - Host name or ID to add or remove from the aggregate
     required: true
requirements: ["shade"]
'''

EXAMPLES = '''
# Add host 'herp' to host aggregate 'derp'
- os_nova_host_agg_hosts:
    cloud: mycloud
    state: present
    name: derp
    host: herp

# Remove host 'herp' from host aggreate 'derp'
- os_nova_host_agg_hosts:
    cloud: mycloud
    state: absent
    name: derp
    host: herp
'''

RETURN = '''
agg:
    description: Dictionary describing the host aggregate.
    returned: On success when I(state) is 'present'
    type: dictionary
    contains:
        id:
            description: Host aggregate ID.
            returned: success
            type: int
            sample: 5
        name:
            description: Host aggregate name.
            returned: success
            type: string
            sample: "derp"
        availability_zone:
            description: Associated availability zone
            returned: success
            type: string
            sample: "haderp"
        deleted:
            description: Whether or not the aggregate is deleted
            returned: success
            type: bool
            sample: False
        deleted_at:
            description: Datestamp of deletion
            returned: success
            type: string
            sample: None
        created_at:
            description: Datestamp of creation
            returned: success
            type: string
            sample: "2016-03-12T00:53:50.000000"
        updated_at:
            description: Datestamp of last update
            returned: success
            type: string
            sample: None
        hosts:
            description: List of hosts associated with the aggregate
            returned: success
            type: list
            sample: []
        metadata:
            description: Metadata keys associated with the aggregate
            returned: success
            type: dict
            sample: {}
hosts:
    description: List of hosts within the host aggregate
    returned: On success when I(state) is 'present'
    type: list
    sample: ['herp', 'derp']
 '''

def _host_exists(agg, host):
    if not host:
        pass
    elif host.service['host'] in agg.hosts:
        return True
    return False

def _system_state_change(module, agg, host):
    state = module.params['state']
    if state == 'present' and not _host_exists(agg, host):
        return True
    if state == 'absent' and _host_exists(agg, host):
        return True
    return False

def _get_aggregate(cloud, name):
    aggs = cloud.nova_client.aggregates.list()
    entities = [x for x in aggs if x.id == name or x.name == name]
    if not entities:
        return None
    if len(entities) > 1:
        raise exc.OpenStackCloudException(
            "Multiple matches found for %s" % name)
    return entities[0]

def _get_host(cloud, host):
    hyps = cloud.nova_client.hypervisors.list()
    entities = [x for x in hyps if
                x.id == host or
                x.hypervisor_hostname == host or
                x.service['host'] == host]
    if not entities:
        return None
    if len(entities) > 1:
        raise exc.OpenStackCloudException(
            "Multiple matches found for %s" % host)
    return entities[0]


def main():
    argument_spec = openstack_full_argument_spec(
        state        = dict(required=False, default='present',
                            choices=['absent', 'present']),
        name         = dict(required=True),
        host         = dict(required=True),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    state = module.params['state']
    name = module.params['name']
    hostname_or_id = module.params['host']

    try:
        cloud = shade.operator_cloud(**module.params)
        agg = _get_aggregate(cloud, name)
        host = _get_host(cloud, hostname_or_id)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, agg, host))

        if state == 'present':
            for resource in ((host, hostname_or_id), (agg, name)):
                if not resource[0]:
                    module.fail_json(msg="No matches found for %s" %
                                     resource[1])
            if not _host_exists(agg, host):
                agg = cloud.nova_client.aggregates.add_host(
                        aggregate=agg,
                        host=host.service['host'])
                changed=True
            else:
                changed=False

            module.exit_json(changed=changed,
                             agg=agg.to_dict(),
                             hosts=agg.hosts)

        elif state == 'absent':
            if not host or not agg:
                module.exit_json(changed=False)
            elif _host_exists(agg, host):
                agg = cloud.nova_client.aggregates.remove_host(
                        aggregate=agg,
                        host=host.service['host'])
                module.exit_json(changed=True)
            else:
                module.exit_json(changed=False)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
