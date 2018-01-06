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
module: keystone_identity_provider
short_description: register identity provider on keystone
description:
  - This module registers an identity provider on keystone
options:
  identity_provider_id:
    description:
        - A globally unique id to identify the identity provider
          example -idp_id
    required: true
  remote_ids:
    description:
        - a list of remote ids for the identity provider
          example -[{ name: aml, remote_ids: "https://example.example/auth/sp2s/samlidp/saml2"}]
    required: true
  enabled:
    description:
      - A value of True enables the identity provider and False disables it.
    default: True
  description:
    description:
      The description of the identity provider.
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


def _needs_update(module, identity_provider):
    """Check for differences in the updatable values.

    Note: Names cannot be updated.
    """
    params_dict = dict(remote_ids='remote_ids',
                       enabled='enabled',
                       description='description')
    for idp_attr, module_attr in params_dict.items():
        module_val = module.params.get(module_attr, None)
        if module_val != getattr(identity_provider, idp_attr, None):
            return True
    return False


def _system_state_change(module, identity_provider):
    state = module.params['state']
    if state == 'present':
        if not identity_provider:
            return True
        return _needs_update(module, identity_provider)
    if state == 'absent' and identity_provider:
        return True
    return False


def _get_cloud(**kwargs):
    cloud_shade = shade.operator_cloud(**kwargs)
    cloud_shade.cloud_config.config['identity_api_version'] = '3'
    cloud = ShadePlaceholder(cloud_shade.keystone_client)
    return cloud


class ShadePlaceholder(object):
    def __init__(self, keystone_client):
        self.client = keystone_client

    def get_identity_provider(self, idp_id):
        for idp in self.client.federation.identity_providers.list():
            if getattr(idp, 'id') == idp_id:
                return idp
        return None

    def create_identity_provider(
            self, idp_id, enabled, description, remote_ids):
        identity_provider = self.client.federation.identity_providers.create(
            id=idp_id,
            enabled=enabled,
            description=description,
            remote_ids=remote_ids)
        return identity_provider

    def update_identity_provider(
            self, idp_id, enabled, description, remote_ids):
        identity_provider = self.client.federation.identity_providers.update(
            identity_provider=idp_id,
            enabled=enabled,
            description=description,
            remote_ids=remote_ids)
        return identity_provider

    def delete_identity_provider(self, idp_id):
        self.client.federation.identity_providers.\
        delete(identity_provider=idp_id)


def main():
    argument_spec = openstack_full_argument_spec(
        identity_provider_id=dict(required=True),
        description=dict(default=None, required=False),
        remote_ids=dict(default=None, type='list', required=False),
        enabled=dict(required=False, type='bool', default=True),
        state=dict(default='present', choices=['absent', 'present']),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    idp_id = module.params['identity_provider_id']
    enabled = module.params['enabled']
    description = module.params['description']
    remote_ids = module.params['remote_ids']

    state = module.params['state']
    try:
        cloud = _get_cloud(**module.params)
        identity_provider = cloud.get_identity_provider(idp_id)

        if module.check_mode:
            changed = _system_state_change(module, identity_provider)
            module.exit_json(changed=changed)

        changed = False
        if state == 'present':
            if not identity_provider:
                identity_provider = cloud.create_identity_provider(
                    idp_id, enabled, description, remote_ids)
                changed = True
            else:
                if _needs_update(module, identity_provider):
                    identity_provider = cloud.update_identity_provider(
                        idp_id, enabled, description, remote_ids)
                    changed = True
        module.exit_json(
            changed=changed,
            identity_provider=[idp_id, enabled, description, remote_ids])
        if state == 'absent':
            if identity_provider:
                cloud.delete_identity_provider(idp_id)
                changed = True
            module.exit_json(changed=changed)

    except Exception as e:
        module.fail_json(msg="identity provider failed: %s" % str(e))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
