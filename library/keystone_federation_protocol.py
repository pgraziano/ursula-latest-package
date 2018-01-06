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
author: Nithya Narengan
module: keystone_federation_protocol
short_description: register keystone protocol
description:
  - This module registers a protocol for federation on keystone
options:
  protocol_id:
    description:
        - name for the protocol
          example -saml2
    required: true
  mapping:
    description:
        - name of an existing mapping that the protocol should be tied to
          example -federation_mapping
    required: true
  identity_provider:
    description:
        - name of an existing identity provider that the protocol should
          be tied to
          example -idp
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


def _needs_update(module, protocol):
    """Check for differences in the updatable values.
    Note: protocol_ids cannot be updated.
    """
    mapping = module.params.get('mapping', None)
    return mapping != getattr(protocol, 'mapping_id', None)


def _system_state_change(module, protocol):
    state = module.params['state']
    if state == 'present':
        if not protocol:
            return True
        return _needs_update(module, protocol)
    if state == 'absent' and protocol:
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

    def _get_identity_provider(self, identity_provider_id):
        for idp in self.client.federation.identity_providers.list():
            if getattr(idp, 'id') == identity_provider_id:
                return idp
        return None

    def _get_mapping(self, mapping_id):
        for mapping in self.client.federation.mappings.list():
            if getattr(mapping, 'id') == mapping_id:
                return mapping
        return None

    def get_protocol(self, protocol_id, idp, mapping_id):
        for protocol in self.client.federation.protocols.list(idp):
            if getattr(protocol, 'id') == protocol_id:
                return protocol
        return None

    def create_protocol(self, protocol_id, idp, mapping_id):
        identity_provider = self._get_identity_provider(idp)
        mapping = self._get_mapping(mapping_id)
        protocol = self.client.federation.protocols.create(
            protocol_id=protocol_id,
            identity_provider=identity_provider,
            mapping=mapping)
        return protocol

    def update_protocol(self, protocol_id, idp, mapping):
        protocol = self.client.federation.protocols.update(
            protocol=protocol_id,
            mapping=mapping,
            identity_provider=idp)

        return protocol

    def delete_protocol(self, protocol_id, idp):
        identity_provider = self._get_identity_provider(idp)
        protocol = self.get_protocol(self, protocol_id, idp)
        self.client.federation.protocols.\
        delete(identity_provider=identity_provider, protocol=protocol)


def main():
    argument_spec = openstack_full_argument_spec(
        protocol_id=dict(required=True),
        mapping=dict(default=None, required=True),
        identity_provider=dict(default=None, required=True),
        state=dict(default='present', choices=['absent', 'present']),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    protocol_id = module.params['protocol_id']
    mapping = module.params['mapping']
    idp = module.params['identity_provider']

    state = module.params['state']
    try:
        cloud = _get_cloud(**module.params)
        protocol = cloud.get_protocol(protocol_id, idp, mapping)

        if module.check_mode:
            changed = _system_state_change(module, protocol)
            module.exit_json(changed=changed)

        changed = False
        if state == 'present':
            if not protocol:
                protocol = cloud.create_protocol(protocol_id, idp, mapping)
                changed = True
            else:
                if _needs_update(module, protocol):
                    protocol = cloud.update_protocol(protocol_id, idp, mapping)
                    changed = True
        module.exit_json(
            changed=changed,
            protocol=[protocol_id, idp, mapping])
        if state == 'absent':
            if protocol:
                cloud.delete_protocol(protocol_id)
                changed = True
            module.exit_json(changed=changed)

    except Exception as e:
        module.fail_json(msg="Keystone protocol failed: %s" % str(e))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
