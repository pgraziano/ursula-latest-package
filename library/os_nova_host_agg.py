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
module: os_nova_host_agg
short_description: Manage OpenStack compute host aggregates
extends_documentation_fragment: openstack
version_added: "2.1"
author: "Jesse Keating (@iamjkeating)"
description:
   - Add or remove host aggregates from OpenStack.
options:
   state:
     description:
        - Indicate desired state of the resource.
     choices: ['present', 'absent']
     required: false
     default: present
   name:
     description:
        - Host aggregate name.
     required: true
   az:
     description:
        - Availability zone to associate with this host aggregate
     required: false
     default: null
requirements: ["shade"]
'''

EXAMPLES = '''
# Create 'derp' host aggregate
- os_nova_host_agg:
    cloud: mycloud
    state: present
    name: derp

# Delete 'derp' host aggregate
- os_nova_host_agg:
    cloud: mycloud
    state: absent
    name: derp

# Create 'derp' host aggregate with 'haderp' availability zone
- os_nova_host_agg:
    cloud: mycloud
    state: present
    name: derp
    az: haderp
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
'''


def _system_state_change(module, agg):
    state = module.params['state']
    if state == 'present' and not agg:
        return True
    if state == 'absent' and agg:
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


def main():
    argument_spec = openstack_full_argument_spec(
        state        = dict(required=False, default='present',
                            choices=['absent', 'present']),
        name         = dict(required=True),
        az           = dict(required=False),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    state = module.params['state']
    name = module.params['name']
    az = module.params['az']

    try:
        cloud = shade.operator_cloud(**module.params)
        agg = _get_aggregate(cloud, name)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, agg))

        if state == 'present':
            if not agg:
                agg = cloud.nova_client.aggregates.create(
                    name=name,
                    availability_zone=az,
                )
                changed=True
            else:
                changed=False

            module.exit_json(changed=changed,
                             agg=agg.to_dict(),
                             id=agg.id)

        elif state == 'absent':
            if agg:
                cloud.nova_client.aggregates.delete(agg)
                module.exit_json(changed=True)
            module.exit_json(changed=False)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
