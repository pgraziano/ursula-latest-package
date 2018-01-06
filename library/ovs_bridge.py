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

import re
import subprocess


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(default=None, required=True),
            state=dict(default='present'),
        )
    )

    try:
        if not re.match('\w+', module.params['name']):
            module.fail_json(msg="invalid bridge name: %s" %
                             (module.params['name']))

        cmd = ["which", "ovs-vsctl"]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        ovs_cmd = p.stdout.readlines()
        if len(ovs_cmd) == 0:
            module.fail_json(msg="ovs-vsctl could not be found")

        ovs_cmd = ovs_cmd[0].strip()
        cmd = [ovs_cmd, "list-br"]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        bridges = p.stdout.readlines()
        for bridge in bridges:
            if bridge.strip() == module.params['name']:
                module.exit_json(changed=False, result="ok")

        cmd = [ovs_cmd, "add-br", module.params['name']]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            module.fail_json(msg="failed to create bridge. out: %s; err: %s" %
                             (out, err))
        module.exit_json(changed=True, result="changed")
    except Exception as e:
        module.fail_json(msg="ovs_bridge error: %s" % (str(e)))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *

main()
