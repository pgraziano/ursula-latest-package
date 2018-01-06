#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2014, Blue Box Group, Inc.
# Copyright 2014, Craig Tracey <craigtracey@gmail.com>
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

import os
import traceback

from hashlib import md5
from jinja2 import Environment

SYSTEMD_TEMPLATE = """
[Unit]
{% if description -%}
Description={{ description }}
{% endif %}
After={{ after }}

[Install]
WantedBy={{ wanted_by }}
{% if alias -%}
Alias={{ alias }}.service
{% endif %}

[Service]
{% if environment_file -%}
EnvironmentFile={{ environment_file }}
{% endif %}
{% if environments -%}
{% for environment in environments %}
Environment={{ environment }}
{% endfor %}
{% endif -%}
Type={{ type }}
{% if notify_access -%}
NotifyAccess={{ notify_access }}
{% endif %}
{% if limit_nofile -%}
LimitNOFILE={{ limit_nofile }}
{% endif %}
{% if user -%}
User={{ user }}
{% endif %}
{% if restart -%}
Restart={{ restart }}
{% endif %}
{% if restart_secs -%}
RestartSec={{ restart_secs }}
{% endif %}
{% if restart_secs -%}
PIDFile={{ pidfile }}
{% endif %}
# Start main service
ExecStart={{ cmd }} {{ args }}
{% if prestart_script -%}
ExecStartPre={{ prestart_script }}
{% endif %}
{% if kill_mode -%}
KillMode={{ kill_mode }}
{% endif %}
{% if kill_signal -%}
KillSignal={{ kill_signal }}
{% endif %}
#ExecStop=
#ExecStopPost=
#ExecReload=
TimeoutStartSec={{ timeout_start_secs }}
TimeoutStopSec={{ timeout_stop_secs }}

"""

def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(default=None, required=True),
            cmd=dict(default=None, required=True),
            environments=dict(default=None, type='list'),
            environment_file=dict(default=None),
            args=dict(default=None),
            user=dict(default=None),
            description=dict(default=None),
            after=dict(default='network.target syslog.target'),
            wanted_by=dict(default='multi-user.target'),
            alias=dict(default=None),
            type=dict(default='simple', choices=['simple',
                                                 'forking', 'oneshot', 'dbus',
                                                 'notify', 'idle']),
            restart=dict(default=None, choices=['always', 'on-success',
                                                'on-failure', 'on-abnormal',
                                                'on-abort"', 'on-watchdog']),
            restart_secs=dict(default=None),
            notify_access=dict(default=None, choices=['none', 'main', 'all']),
            config_dirs=dict(default=None),
            config_files=dict(default=None),
            kill_signal=dict(default=None),
            state=dict(default='present', choices=['present', 'absent']),
            prestart_script=dict(default=None),
            timeout_start_secs=dict(default='120'),
            timeout_stop_secs=dict(default='120'),
            kill_mode=dict(default=None, choices=['control-group', 'process',
                                                  'mixed', 'none']),
            pidfile=dict(default=None),
            limit_nofile=dict(default=None),
            path=dict(default=None)
        )
    )

    try:
        changed = False
        service_path = None
        if not module.params['path']:
            service_path = '/etc/systemd/system/%s.service' % module.params['name']
        else:
            service_path = module.params['path']

        if module.params['state'] == 'absent':
            if os.path.exists(service_path):
                os.remove(service_path)
                changed = True
            if not changed:
                module.exit_json(changed=False, result="ok")
            else:
                os.system('systemctl daemon-reload')
                module.exit_json(changed=True, result="changed")

        args = ' '
        if module.params['args'] or module.params['config_dirs'] or \
           module.params['config_files']:
            if module.params['args']:
                args += module.params['args']

            if module.params['config_dirs']:
                for directory in module.params['config_dirs'].split(','):
                    args += '--config-dir %s ' % directory

            if module.params['config_files']:
                for filename in module.params['config_files'].split(','):
                   args += '--config-file %s ' % filename

        template_vars = module.params
        template_vars['args'] = args

        env = Environment().from_string(SYSTEMD_TEMPLATE)
        rendered_service = env.render(template_vars)

        if os.path.exists(service_path):
            file_hash = md5(open(service_path, 'rb').read()).hexdigest()
            template_hash = md5(rendered_service).hexdigest()
            if file_hash == template_hash:
                module.exit_json(changed=False, result="ok")

        with open(service_path, "w") as fh:
            fh.write(rendered_service)
        os.system('systemctl daemon-reload')
        module.exit_json(changed=True, result="created")
    except Exception as e:
        formatted_lines = traceback.format_exc()
        module.fail_json(msg="creating the service failed: %s" % (str(e)))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *

main()
