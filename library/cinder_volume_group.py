#!/usr/bin/python
#coding: utf-8 -*-

DOCUMENTATION = '''
---
author: Jesse Keating and Dustin Lundquist
module: cinder_volume_group
short_description: Configure LVM volume groups
description:
  - This module creates a LVM VG for Cinder to use
options:
  size:
    description:
      - The size of the VG file to create
    required: true
  file:
    description:
      - The file path on the filesystem to create
    required: false
    aliases: ["dest"]
  vgname:
    description:
      - The name for the volume group
    default: cinder-volumes
'''

EXAMPLES = '''
# create a volume group for cinder, named `cinder-volumes`,
# backed by a file mounted over loop device

- cinder_volume_group: path=/some/path/foo size=100G
'''

import os
import re
import subprocess

def _is_device_type(device, device_type, module):
    if not os.path.exists(device):
        return False
    if os.path.exists('/usr/bin/hd'):
        hd = '/usr/bin/hd'
    else:
        hd = '/bin/hexdump'
    cmd = [hd, '-n', '16384', device]
    rc, out, err = module.run_command(cmd, check_rc=True)
    return re.search(device_type, out)


def is_luks(device, module):
    return _is_device_type(device, 'LUKS', module)


def is_lvm_pv(device, module):
    return _is_device_type(device, 'LMV2', module)


def vgexists(name, module):
    cmd = ['vgs', name]
    rc, out, err = module.run_command(cmd)
    return bool(rc == 0)


def main():
    module = AnsibleModule(
        argument_spec  = dict(
            size       = dict(required=True),
            file       = dict(required=True, aliases=['dest']),
            vgname     = dict(default='cinder-volumes'),
        ),
    )

    size = module.params.get('size')
    dest = module.params.get('file')
    vgname = module.params.get('vgname')

    # see if we have this vg already
    if vgexists(vgname, module):
        module.exit_json(changed=False)

    # Check if our dest already exists
    if os.path.exists(dest):
        module.fail_json(msg="Destination file %s already exists" % dest)

    # Create dest file
    cmd = ['truncate', '-s', size, dest]
    rc, out, err = module.run_command(cmd, check_rc=True)
    try:
        os.chmod(dest, 0700)
    except Exception, e:
        module.fail_json(msg="Unable to set permissions: %s" % e)

    # Setup loop device

    rc, out, err = module.run_command('losetup -f', check_rc=True)

    device = out.strip('\n')

    #if os.path.exists('/dev/loop0'):
    #    device = '/dev/loop0'
    #elif os.path.exists('/dev/loop1'):
    #    device = '/dev/loop1'

    if os.path.exists('/etc/init/losetup.conf'):
        lines = ['start on filesystem', 'task',
                 'exec losetup %s %s' % (device, dest)]
        try:
            with open('/etc/init/losetup.conf', 'w') as f:
                f.write('\n'.join(lines) + '\n')
        except Exception, e:
            module.fail_json(msg="Unable to write losetup file: %s" % e)

    cmd = ['losetup', device, dest]
    rc, out, err = module.run_command(cmd, check_rc=True)

    if is_luks('/dev/mapper/%s' % vgname, module):
        module.fail_json(msg="%s is a LUKS volume" % device)

    if is_lvm_pv(device, module):
        module.fail_json(msg="%s is already a LVM PV" % device)
    else:
        cmd = ['vgcreate', vgname, device]
        rc, out, err = module.run_command(cmd, check_rc=True)

    if not vgexists(vgname, module):
        module.fail_json(msg="Unable to setup %s" % vgname)

    module.exit_json(changed=True, file=dest)


# this is magic, see lib/ansible/module.params['common.py
from ansible.module_utils.basic import *

main()
