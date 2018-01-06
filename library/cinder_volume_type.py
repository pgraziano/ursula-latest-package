#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2013, Blue Box Group, Inc.
# Copyright 2013, Craig Tracey <craigtracey@gmail.com>
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
module: cinder_volume_type
short_description: Create cinder volume types
description:
   - cinder_volume_types
options:
   login_username:
     description:
        - login username to authenticate to keystone
     required: true
     default: admin
   login_password:
     description:
        - password of login user
     required: true
     default: 'password'
   login_tenant_id:
     description:
        - the tenant id of the login user
     required: true
     default: None
   auth_url:
     description:
        - the keystone url for authentication
     required: false
     default: 'http://127.0.0.1:5001/v2.0/'
   encryption_type:
     description:
        - flag indicating whether this is a encrption type or not
     required: false
     default: false
   volume_type:
     description:
        - the name of the cinder volume type
     required: true
     default: None
   provider:
     decription:
       - the module path to the Nova encryption provider
     required: false
     default: None
   control_location:
     decription:
       - the control location to user in the Nova encryption provider
     required: false
     default: None
   cipher:
     decription:
       - the cipher to use in the Nova encryption provider
     required: None
     default: None
   key_size:
     decription:
       - the key size to use in the Nova encryption provider
     required: None
     default: None
   extra_specs:
     description:
       - A dictionary of extra specs to add to the volume type.
     required: false
     default: None
requirements: [ "python-cinderclient", "python-keystoneclient" ]
'''

EXAMPLES = '''
- cinder_volume_type: |
    login_username=admin
    login_password=password
    login_tenant_id=123456789
    auth_url=http://keystone:5001/v2.0
    volume_type=encrypted-aes-256
    extra_specs="volume_backend_name=some-name"
'''

try:
    from keystoneclient.v2_0 import client as ksclient
    from cinderclient.v2 import client
except ImportError as e:
    print("failed=True msg='python-cinderclient is required'")


# FIXME(cmt): the fact that we need this is totally ridiculous. cinderclient
# does not accept tenant_name as a parameter. So we are forced to lookup the
# tenant's id. seriously?!
def _get_tenant_id(module, **kwargs):
    tenant_id = None
    try:
        keystone = ksclient.Client(username=kwargs.get('login_username'),
                                   password=kwargs.get('login_password'),
                                   insecure=kwargs.get('insecure'),
                                   auth_url=kwargs.get('auth_url'))
        for tenant in keystone.tenants.list():
            if tenant.name == kwargs.get('login_tenant_name'):
                tenant_id = tenant.id
    except Exception as e:
        module.fail_json(msg="error authenticating to keystone: %s" % str(e))
    return tenant_id


def _get_cinderclient(module, **kwargs):
    cinderclient = None
    tenant_id = _get_tenant_id(module, **kwargs)
    try:
        cinderclient = client.Client(username=kwargs.get('login_username'),
                                     insecure=kwargs.get('insecure'),
                                     api_key=kwargs.get('login_password'),
                                     tenant_id=tenant_id,
                                     auth_url=kwargs.get('auth_url'))
    except Exception as e:
        module.fail_json(msg="error authenticating to cinder: %s" % str(e))
    return cinderclient


def _create_volume_type(module, cinderclient, type_name):
    volume_type_id = _get_volume_type_id(cinderclient, type_name)
    if volume_type_id:
        module.exit_json(changed=False, result="unchanged")
    return cinderclient.volume_types.create(type_name)


def _volume_type_set_keys(volume_type, extra_specs):
    if extra_specs is not None:
        try:
            volume_type.set_keys(extra_specs)
        except Exception as e:
            raise e


def _get_volume_type_id(cinderclient, type_name):
    volume_type_id = None
    volume_types = cinderclient.volume_types.list()
    for volume_type in volume_types:
        if volume_type.name == type_name:
            volume_type_id = volume_type.id
    return volume_type_id


def _get_encrypted_volume_type_id_name(cinderclient, volume_type_id):
    enc_volume_types = cinderclient.volume_encryption_types.list()
    for enc_volume_type in enc_volume_types:
        if enc_volume_type.volume_type_id == volume_type_id:
            return enc_volume_type
    return None


def _create_encrypted_volume_type(module, cinderclient, volume_type, provider,
                                  control_location=None, cipher=None,
                                  key_size=None):
    volume_type_id = _get_volume_type_id(cinderclient, volume_type)
    if not volume_type_id:
        _create_volume_type(module, cinderclient, volume_type)

    volume_type_id = _get_volume_type_id(cinderclient, volume_type)
    if not volume_type_id:
        raise ValueError("volume type '%s' not found and could not be created" % volume_type)

    enc_volume_type = _get_encrypted_volume_type_id_name(cinderclient,
                                                         volume_type_id)
    if enc_volume_type:
        if (provider == enc_volume_type.provider and
            control_location == enc_volume_type.control_location and
            cipher == enc_volume_type.cipher and
            int(key_size) == enc_volume_type.key_size):
            module.exit_json(changed=False, result="unchanged")

    # FIXME(cmt) this should not be necessary but seems to be broken
    # in cinder itself, so force it here.
    possible_control_locs = ('front-end', 'back-end')
    if control_location not in possible_control_locs:
        raise ValueError("control_location must be one of %s" %
                         " or ".join(possible_control_locs))

    spec = {
        'provider': provider,
        'control_location': control_location,
        'cipher': cipher,
        'key_size': int(key_size)
    }
    cinderclient.volume_encryption_types.create(volume_type_id, spec)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            login_username=dict(default=None),
            login_password=dict(default=None),
            login_tenant_name=dict(default=None),
            auth_url=dict(default='http://127.0.0.1:5001/v2.0/'),
            volume_type=dict(required=True),
            encryption_type=dict(default=False, type='bool'),
            provider=dict(default=None),
            cipher=dict(default=None),
            key_size=dict(default=None),
            control_location=dict(default=None),
            extra_specs=dict(default=None, type='dict'),
            insecure=dict(default=False, type='bool'),
        )
    )

    cinderclient = _get_cinderclient(module, **module.params)
    try:
        if module.params['encryption_type']:
            _create_encrypted_volume_type(module, cinderclient,
                                          module.params['volume_type'],
                                          module.params['provider'],
                                          module.params['control_location'],
                                          module.params['cipher'],
                                          module.params['key_size'])
        else:
            volume_type = _create_volume_type(module, cinderclient,
                                              module.params['volume_type'])
            _volume_type_set_keys(volume_type, module.params.get(
                                  'extra_specs'))
        module.exit_json(changed=True, result="created")
    except Exception as e:
        module.fail_json(msg="creating the volume type failed: %s" % str(e))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *

main()
