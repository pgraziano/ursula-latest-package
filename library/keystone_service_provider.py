#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2016, IBM
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
try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
author: Elvin Tubillara
module: keystone_service_provider
short_description: register sp on keystone idp
description:
  - This module registers a keystone service provider on the keystone
    identity provider.
options:
  service_provider_id:
    description:
        - A globally unique id to identify the service provider
          example -sp.id
    required: true
  service_provider_url:
    description:
        - URL that is found in the service provider's metadata
          (Which is usually found
          in https://keystone.sp/Shibboleth.sso/metadata)
          example -https://keystone.sp/Shibboleth.sso/SAML2/ECP
    required: true
  service_provider_auth_url:
    description:
        - URL that is used to authenticate with the identity provider
          This URL should be available once the idp registered on the sp
          example -'http://keystone.sp/v3/OS-FEDERATION/'
                 'identity_providers/keystone-idp/protocols/saml2/auth'
    required: true
  enabled:
    description:
      - A value of True enables the service provider and False disables it.
    default: True
  description:
    description:
      The description of the service provider.
  state:
    description:
       - Indicate desired state of the resource
    choices: ['present', 'absent']
    default: present
'''


def _needs_update(module, service_provider):
    """Check for differences in the updatable values.

    Note: Names cannot be updated.
    """
    params_dict = dict(sp_url='service_provider_url',
                       auth_url='service_provider_auth_url',
                       enabled='enabled', description='description')
    for sp_attr, module_attr in params_dict.items():
        module_val = module.params.get(module_attr, None)
        if module_val != getattr(service_provider, sp_attr, None):
            return True
    return False


def _system_state_change(module, service_provider):
    state = module.params['state']
    if state == 'present':
        if not service_provider:
            return True
        return _needs_update(module, service_provider)
    if state == 'absent' and service_provider:
        return True
    return False


def _get_cloud(**kwargs):
    cloud_shade = shade.openstack_cloud(**kwargs)
    cloud_shade.cloud_config.config['identity_api_version'] = '3'
    cloud = ShadePlaceholder(cloud_shade.keystone_client)
    return cloud


class ShadePlaceholder(object):
    def __init__(self, keystone_client):
        self.client = keystone_client

    def get_service_provider(self, sp_id):
        for sp in self.client.federation.service_providers.list():
            if getattr(sp, 'id') == sp_id:
                return sp
        return None

    def create_service_provider(
            self, sp_id, sp_url, sp_auth_url, enabled, description):
        service_provider = self.client.federation.service_providers.create(
            id=sp_id, sp_url=sp_url, auth_url=sp_auth_url,
            enabled=enabled, description=description)
        return service_provider

    def update_service_provider(
            self, sp_id, sp_url, sp_auth_url, enabled, description):
        service_provider = self.client.federation.service_providers.update(
            service_provider=sp_id, sp_url=sp_url, auth_url=sp_auth_url,
            enabled=enabled, description=description)
        return service_provider

    def delete_service_provider(self, sp_id):
        self.client.federation.service_providers.delete(service_provider=sp_id)


def main():
    argument_spec = openstack_full_argument_spec(
        service_provider_id=dict(required=True),
        service_provider_url=dict(required=True),
        service_provider_auth_url=dict(required=True),
        enabled=dict(required=False, type='bool', default=True),
        description=dict(required=False, default=None),
        state=dict(default='present', choices=['absent', 'present']),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    sp_id = module.params['service_provider_id']
    sp_url = module.params['service_provider_url']
    sp_auth_url = module.params['service_provider_auth_url']
    enabled = module.params['enabled']
    description = module.params['description']

    state = module.params['state']
    try:
        cloud = _get_cloud(**module.params)
        service_provider = cloud.get_service_provider(sp_id)

        if module.check_mode:
            changed = _system_state_change(module, service_provider)
            module.exit_json(changed=changed)

        changed = False
        if state == 'present':
            if not service_provider:
                service_provider = cloud.create_service_provider(
                    sp_id, sp_url, sp_auth_url, enabled, description)
                changed = True
            else:
                if _needs_update(module, service_provider):
                    service_provider = cloud.update_service_provider(
                        sp_id, sp_url, sp_auth_url, enabled, description)
                    changed = True
        module.exit_json(
            changed=changed,
            service_provider=[service_provider.id, service_provider.sp_url,
                              service_provider.auth_url, enabled, description])
        if state == 'absent':
            if service_provider:
                cloud.delete_service_provider(sp_id)
                changed = True
            module.exit_json(changed=changed)

    except Exception as e:
        module.fail_json(msg="service provider failed: %s" % str(e))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
