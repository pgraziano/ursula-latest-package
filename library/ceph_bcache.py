#!/usr/bin/python
#coding: utf-8 -*-

DOCUMENTATION = """
---
author: Michael Sambol, Siva Nandyala
module: ceph_bcache
short_description: Activates OSDs in a Bcache Ceph cluster
description: Because of the nature of a Bcache Ceph cluster,
             a "stateless" approach was taken. This module was
             largely based on: http://redpill-linpro.com/sysadvent/2015/12/18/stateless-osd-servers.html
options:
  disks:
    description:
      - List of disks. Defined as ceph.disks in the env.
    required: True
  ssd_device:
    description:
      - The SSD device. Defined as ceph.bcache_ssd_device in the env.
    required: True
  journal_guid:
    description:
      - GUID of journal partition. Defined by ceph community in /lib/udev/rules.d/95-ceph-osd.rules.
    required: True
"""

EXAMPLES = """
- name: activate osds
  ceph_bcache:
    disks: "{{ ceph.disks }}"
    ssd_device: "{{ ceph.bcache_ssd_device }}"
    journal_guid: "{{ ceph.journal_guid }}
"""

import os
import re


def main():
    module = AnsibleModule(
        argument_spec=dict(
            disks=dict(type='list', required=True),
            ssd_device=dict(required=True),
            ceph_init_ssd=dict(type='bool', required=True),
            journal_guid=dict(required=True),
        ),
    )
    disks = module.params.get('disks')
    ssd_device = module.params.get('ssd_device')
    ceph_init_ssd = module.params.get('ceph_init_ssd')
    journal_guid = module.params.get('journal_guid')
    changed = False
    uuids_in_order = [None] * len(disks)

    # the disks have symlinks to /dev/bcacheX. we need the disks
    # in increasing order by X.
    # Use regex to determine the bcache index

    for subdir, dirs, files in os.walk('/dev/disk/by-uuid/'):
      for uuid in files:
        disk = os.path.join(subdir, uuid)
        path = os.path.realpath(disk)

        if 'bcache' in path:
          bcache_index = int(re.search(r'\d+$', path).group(0))
          uuids_in_order.pop(bcache_index)
          uuids_in_order.insert(bcache_index,uuid)
    cmd = ['grep', 'ceph', "/etc/fstab"]
    rc, bcache_fstabs, err = module.run_command(cmd)
    bcache_fstabs = bcache_fstabs.split('\n')

    for i in range(0, len(uuids_in_order)):
      # running this command with the uuid argument will return the same value each time
      cmd = ['ceph', 'osd', 'create', uuids_in_order[i]]
      rc, out, err = module.run_command(cmd, check_rc=True)
      osd_id = out.rstrip()

      bcache_index = i
      partition_index = int(osd_id) % len(disks) + 1

      # we configure new journal here if osd dir already exists
      if os.path.exists('/var/lib/ceph/osd/ceph-' + osd_id) and ceph_init_ssd:
        cmd = ['chown', 'ceph:ceph',
               '/dev/' + ssd_device + str(partition_index)]
        rc, out, err = module.run_command(cmd, check_rc=True)

        cmd = ['sgdisk', '-t', str(partition_index) + ':' + journal_guid,
               '/dev/' + ssd_device]
        rc, out, err = module.run_command(cmd, check_rc=True)

        cmd = ['ceph-osd', '-i', osd_id, '--mkjournal']
        rc, out, err = module.run_command(cmd, check_rc=True)

      # if first time running 'ceph osd create' against this uuid, create the osd dir
      # and handle rest of activation. if directory exists, the device has already
      # been activated.
      if not os.path.exists('/var/lib/ceph/osd/ceph-' + osd_id):
        os.makedirs('/var/lib/ceph/osd/ceph-' + osd_id)
        changed = True

        cmd = ['mount', '/dev/bcache' + str(bcache_index), '/var/lib/ceph/osd/ceph-' + osd_id]
        rc, out, err = module.run_command(cmd, check_rc=True)

        cmd = ['ceph-osd', '-i', osd_id, '--mkfs', '--mkkey', '--osd-uuid', uuids_in_order[i]]
        rc, out, err = module.run_command(cmd, check_rc=True)

        os.remove('/var/lib/ceph/osd/ceph-' + osd_id + '/journal')

        if 'nvme' in ssd_device:
            cmd = ['chown', 'ceph:ceph', '/dev/' + ssd_device + 'p' + str(partition_index)]
        else:
            cmd = ['chown', 'ceph:ceph', '/dev/' + ssd_device + str(partition_index)]
        rc, out, err = module.run_command(cmd, check_rc=True)

        cmd = ['sgdisk', '-t', str(partition_index) + ':' + journal_guid, '/dev/' + ssd_device]
        rc, out, err = module.run_command(cmd, check_rc=True)

        if 'nvme' in ssd_device:
            cmd = ['ln', '-s', '/dev/' + ssd_device + 'p' + str(partition_index), '/var/lib/ceph/osd/ceph-' + osd_id + '/journal']
        else:
            cmd = ['ln', '-s', '/dev/' + ssd_device + str(partition_index), '/var/lib/ceph/osd/ceph-' + osd_id + '/journal']
        rc, out, err = module.run_command(cmd, check_rc=True)

        cmd = ['ceph-osd', '-i', osd_id, '--mkjournal']
        rc, out, err = module.run_command(cmd, check_rc=True)

        cmd = ['umount', '/var/lib/ceph/osd/ceph-' + osd_id]
        rc, out, err = module.run_command(cmd, check_rc=True)

        cmd = ['ceph-disk', 'activate', '/dev/bcache' + str(bcache_index)]
        rc, out, err = module.run_command(cmd, check_rc=True)

        cmd = ['chown', '-R', 'ceph:ceph', '/var/lib/ceph/osd/ceph-' + osd_id]
        rc, out, err = module.run_command(cmd, check_rc=True)

        bcache_fstabs.append('UUID=%(uuid)s /var/lib/ceph/osd/ceph-%(osd_id)s'
                             ' xfs defaults,noatime,largeio,inode64,swalloc '
                             '0 0' % {'uuid': uuids_in_order[i],
                                      'osd_id': osd_id})

    if changed:
      cmd = ['sed', '-i', '/ceph/d', '/etc/fstab']
      rc, out, err = module.run_command(cmd, check_rc=True)
      # add available mount items
      with open("/etc/fstab", "a") as fstab:
        for mount_item in filter(None, bcache_fstabs):
          if any([ uuid in mount_item for uuid in uuids_in_order]):
            fstab.write(mount_item + '\n') 

    module.exit_json(changed=changed)

from ansible.module_utils.basic import *
main()
