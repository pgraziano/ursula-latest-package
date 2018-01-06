#!/usr/bin/python
#coding: utf-8 -*-

DOCUMENTATION = '''
---
author: Jesse Keating and Dustin Lundquist
module: swift_disk
short_description: Configure Swift disks/partition
description:
  - This module prepares the disk/partition for use with Swift
options:
  dev:
    description:
      - The device to make a swift disk
    required: false
  partition_path:
    description:
      - Complete path to partition to be used for Swift
    required: false
'''

EXAMPLES = '''
# use the sdb disk for swift. it will be formatted to xfs
# and mounted on /srv/node/sdb

- swift_disk: dev=sdb

# use the lvm disk /dev/vgpool/sftmeta. Partition will be formatted
# and mounted on /srv/node/sftmeta

- swift_disk: partition_path=/dev/vgpool/sftmeta
'''

import os
import pwd
import grp

def main():
    module = AnsibleModule(
        argument_spec  = dict(
            dev  = dict(required=False, default=None),
            partition_path = dict(required=False, default=None),
            mount_point = dict(required=False, default=None),
            make_label = dict(required=False, default=False),
        ),
        required_one_of = [['dev', 'partition_path']],
        mutually_exclusive = [['dev', 'partition_path']]
    )

    dev = module.params.get('dev')
    part_path = module.params.get('partition_path')

    dev_path = None

    if not module.params.get('mount_point'):
        mount_point = "/srv/node/"
        if dev is not None:
            dev_path = "/dev/%s" % dev
            part_path = "/dev/%s1" % dev
            mount_point += ("%s1" % dev)
        else:
            # Get the last part of partition path
            mount_point += (part_path.split("/")[-1])
    else:
        mount_point = module.params.get('mount_point')

    if dev_path is not None and not os.path.exists(dev_path):
        module.fail_json(msg="no such device: %s" % dev)

    if os.path.exists(part_path) and os.path.ismount(mount_point):
        module.exit_json(changed=False)

    if dev_path is not None:
        if module.params.get('make_label'):
            cmd = ['parted', '--script', dev_path, 'mklabel', 'gpt']
            rc, out, err = module.run_command(cmd, check_rc=True)    

        # create partitions
        cmd = ['parted', '--script', dev_path, 'mkpart', 'primary', '1', '100%']
        rc, out, err = module.run_command(cmd, check_rc=True)

    # make an xfs
    cmd = ['mkfs.xfs', '-f', '-i', 'size=512', part_path]
    rc, out, err = module.run_command(cmd, check_rc=True)

    # discover uuid
    cmd = ['blkid', '-o', 'value', part_path]
    rc, out, err = module.run_command(cmd, check_rc=True)
    fsuuid = out.splitlines()[0]

    # write fstab
    try:
        with open('/etc/fstab', 'a') as f:
            f.write("UUID=%s %s xfs noatime,nodiratime,nobarrier,logbufs=8 0 0\n" % (fsuuid, mount_point))
    except Exception, e:
        module.fail_json(msg="failed to update fstab: %s" % e)

    # mount point
    os.makedirs(mount_point)

    # mount it
    cmd = ['mount', mount_point]
    rc, out, err = module.run_command(cmd, check_rc=True)

    # chown it
    swuid = pwd.getpwnam('swift').pw_uid
    swgid = grp.getgrnam('swift').gr_gid
    os.chown(mount_point, swuid, swgid)

    module.exit_json(changed=True)

# this is magic, see lib/ansible/module.params['common.py
from ansible.module_utils.basic import *

main()
