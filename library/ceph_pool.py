#!/usr/bin/python
#coding: utf-8 -*-

DOCUMENTATION = """
---
author: Michael Sambol
module: ceph_pool
short_description: Creates ceph pool
description:
  There are three possible outcomes:
    1/ Create a new pool if it doesn't exist
    2/ Nothing: pool already exist
options:
  pool_name:
    description:
      - The pool in question: create it or ensure correct pg count
    required: true
  osds:
    description:
      - The osds count: pg count is calculated based on osd number
    required: true
  target_pgs_per_osd:
    description:
      - The desired PG numbers per OSD
    required: true
  max_pgs_per_osd:
    description:
      - The max PG numbers per OSD which should never be exceeded.
    required: true
  pool_size:
    description:
      - Copies of PGs
    default: 3
"""

EXAMPLES = """
# ceph_pool can only be run on nodes that have an admin keyring
# pool_name = default
- ceph_pool:
    pool_name: default
    osds: "{{ groups['ceph_osds_ssd']|length * ceph.disks|length }}"
    target_pgs_per_osd: "{{ ceph.target_pgs_per_osd }}"
    max_pgs_per_osd: "{{ ceph.max_pgs_per_osd }}"
    pool_size: "{{ ceph.pool_default_size }}"
  register: pool_output
  run_once: true
  delegate_to: "{{ groups['ceph_monitors'][0] }}"
"""

import time

def main():
    module = AnsibleModule(
        argument_spec=dict(
            pool_name=dict(required=True),
            osds=dict(required=True, type='int'),
            target_pgs_per_osd=dict(required=True, type='int'),
            max_pgs_per_osd=dict(required=True, type='int'),
            pool_size=dict(default=3, type='int'),
        ),
    )

    pool_name = module.params.get('pool_name')
    osds = module.params.get('osds')
    target_pgs_per_osd = module.params.get('target_pgs_per_osd')
    max_pgs_per_osd = module.params.get('max_pgs_per_osd')
    pool_size = module.params.get('pool_size')

    # calculate desired pg count
    # read more about pg count here: http://ceph.com/pgcalc/
    total_pg_count = osds * target_pgs_per_osd / pool_size
    i = 0
    desired_pg_count = 0
    # find the number which is power of 2 and larger than total_pg_count
    while desired_pg_count < total_pg_count:
        desired_pg_count = 2**i
        i += 1
    while desired_pg_count * pool_size / osds > max_pgs_per_osd:
        desired_pg_count = desired_pg_count / 2

    # does the pool exist already?
    cmd = ['ceph', 'osd', 'pool', 'get', pool_name, 'pg_num']
    rc, out, err = module.run_command(cmd, check_rc=False)

    # no
    if rc != 0:
        # create the pool
        cmd = ['ceph', 'osd', 'pool', 'create', pool_name,
               str(desired_pg_count), str(desired_pg_count)]
        rc, out, err = module.run_command(cmd, check_rc=True)
        module.exit_json(changed=True, msg="new pool was created")
    # yes
    else:
        module.exit_json(changed=False)

from ansible.module_utils.basic import *
main()
