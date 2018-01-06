#!/bin/bash
#
# check neutron l3 agents on routers
# only run on node with the floating ip

if ifconfig | grep {{ undercloud_floating_ip | default(floating_ip) }} > /dev/null 2>&1; then
  /etc/sensu/plugins/check-neutron-l3-routers.py -r {{ sensu_checks.neutron.check_neutron_l3_routers.max_routers }} \
  -d {{ sensu_checks.neutron.check_neutron_l3_routers.delay_seconds }}
fi;
