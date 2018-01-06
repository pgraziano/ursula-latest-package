#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2016, IBM
# Copyright 2016, Craig Tracey <craigtracey@gmail.com>
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
#

DOCUMENTATION = '''
---
author: Elvin Tubillara
module: keystone_service_provider
short_description: register mapping
description:
  - This module registers a federation mapping on keystone
options:
  mapping_id:
    description:
        - id of the mapping
          example -federation_mapping
    required: true
  rules:
    description:
        - keystone mapping rules
          example : |
              [
                {
                    "local": [
                        {
                            "user": {
                                "name": "{0}"
                            }
                        },
                        {
                            "group": {
                                "domain": {
                                    "name": "Default"
                                },
                                "name": "some_group"
                            }
                        }
                    ],
                    "remote": [
                        {
                            "type": "email"
                        },
                        {
                            "type": "email",
                            "any_one_of": [
                                "example@email.com",

                            ]
                        }
                    ]
                }
            ]
    required: true
  state:
    description:
       - Indicate desired state of the resource
    choices: ['present', 'absent']
    default: present
'''
try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


def _get_cloud(**kwargs):
    cloud_shade = shade.operator_cloud(**kwargs)
    cloud_shade.cloud_config.config['identity_api_version'] = '3'
    cloud = ShadePlaceholder(cloud_shade.keystone_client)
    return cloud


class ShadePlaceholder(object):
    def __init__(self, keystone_client):
        self.client = keystone_client

    def get_mapping(self, mapping_id):
        for mapping in self.client.federation.mappings.list():
            if getattr(mapping, 'id') == mapping_id:
                return mapping
        return None

    def create_mapping(self, mapping_id, rules):
        mapping = self.client.federation.mappings.create(
            mapping_id=mapping_id,
            rules=rules)
        return mapping

    def update_mapping(self, mapping_id, rules):
        mapping = self.client.federation.identity_providers.update(
            mapping_id=mapping_id,
            rules=rules)
        return mapping

    def delete_mapping(self, mapping_id):
        mapping = self.get_mapping(mapping_id)
        self.client.federation.mappings.delete(mapping=mapping)


def main():
    argument_spec = openstack_full_argument_spec(
        mapping_id=dict(required=True),
        rules=dict(required=True, type='list'),
        state=dict(default='present', choices=['absent', 'present']),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    mapping_id = module.params['mapping_id']
    rules = module.params['rules']

    state = module.params['state']
    try:
        cloud = _get_cloud(**module.params)
        mapping = cloud.get_mapping(mapping_id)
        changed = False

        if module.check_mode:
            if state == 'present':
                changed = mapping is not None
            elif state == 'absent':
                changed = mapping is None
            module.exit_json(changed=changed)

        if state == 'present':
            if not mapping:
                mapping = cloud.create_mapping(mapping_id, rules)
                changed = True
            else:
                changed = False
        module.exit_json(
            changed=changed,
            mapping=[mapping_id, rules])
        if state == 'absent':
            if mapping:
                cloud.delete_mapping(mapping_id)
                changed = True
            module.exit_json(changed=changed)

    except Exception as e:
        module.fail_json(msg="Keystone mapping failed: %s" % str(e))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
