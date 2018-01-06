#!/usr/bin/python
#coding: utf-8 -*-
#
# (c) 2014, Craig Tracey <craigtracey@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION = '''
author: Craig Tracey
'''

import os

from subprocess import check_call, CalledProcessError


def _run_ring_command(module, command, builder_file, force, *args):
    cmd = ['swift-ring-builder', builder_file, command] + list(args)
    try:
        rc = subprocess.check_call(cmd)
    except Exception as e:
        module.fail_json(msg="Error running swift-ring-builder command %s'" %
                        (e.message, " ".join(cmd)))

    return True


def swift_ring_create(module, builder_file, part_power, replicas,
                      min_part_hours, force=False):
    return _run_ring_command(module, 'create', builder_file, force,
                             part_power, replicas, min_part_hours)


def swift_ring_add(module, builder_file, zone, ip, port, device_name, meta,
                   weight, force=False):
    device_str = "z%(zone)s-%(ip)s:%(port)s/%(device_name)s_%(meta)s" % \
                 locals()
    return _run_ring_command(module, 'add', builder_file, force,
                             device_str, weight)


def swift_ring_rebalance(module, builder_file, ring_type, force=False):
    if not force and os.path.exists("/etc/swift/%s.ring.gz" % ring_type):
        return False

    return _run_ring_command(module, 'rebalance', builder_file, force)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=True,
                        choices=['create', 'add', 'rebalance']),
            ring_type=dict(required=True,
                           choices=['account', 'container', 'object']),
            builder_file=dict(required=True),
            part_power=dict(required=False),
            replicas=dict(required=False),
            min_part_hours=dict(required=False),
            zone=dict(required=False),
            ip=dict(required=False),
            port=dict(required=False),
            device_name=dict(required=False),
            meta=dict(required=False),
            weight=dict(required=False),
            force=dict(required=False, default=False)
        )
    )

    changed = False
    params = module.params
    if params['action'] == 'create':
        changed = swift_ring_create(module,
                                    params['builder_file'],
                                    params['part_power'],
                                    params['replicas'],
                                    params['min_part_hours'],
                                    params['force'])
    elif params['action'] == 'add':
        changed = swift_ring_add(module,
                                 params['builder_file'],
                                 params['zone'],
                                 params['ip'],
                                 params['port'],
                                 params['device_name'],
                                 params['meta'],
                                 params['weight'],
                                 params['force'])
    elif params['action'] == 'rebalance':
        changed = swift_ring_rebalance(module,
                                       params['builder_file'],
                                       params['ring_type'],
                                       params['force'])

    module.exit_json(changed=changed)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *

main()
