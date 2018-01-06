#!/bin/bash
#
# check swift dispersion
# only run on node with the floating ip

if ifconfig | grep {{ swift_undercloud_floating_ip | default( swift_floating_ip ) }} > /dev/null 2>&1; then
  sudo /etc/sensu/plugins/check-swift-dispersion.py -c 98 -d 99 -o 98 -n 99
fi;
