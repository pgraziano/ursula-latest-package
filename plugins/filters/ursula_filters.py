import os


def ursula_controller_ips(hostvars, groups, controller_name='controller'):
    controller_ips = set()
    for host in groups[controller_name]:
        controller_primary_interface = hostvars[host]['primary_interface']
        ip = hostvars[host][controller_primary_interface]['ipv4']['address']
        controller_ips.add(ip)
    return sorted(list(controller_ips))


def ursula_memcache_hosts(hostvars, groups, memcache_port,
                          controller_name='controller'):
    controller_ips = ursula_controller_ips(hostvars, groups, controller_name)
    host_strings = ['%s:%s' % (c, memcache_port) for c in controller_ips]
    return ','.join(host_strings)


def ursula_package_path(project, version):
    package_name_format = "openstack-%(version)s" % locals()
    path = os.path.join("/opt/bbc", package_name_format, project)
    return path


def remove_vlan_tag(interface):
    return interface.split(".")[0]


def net_physical_devices(interface):
    devices = []
    if 'slaves' in interface:
        devices = interface['slaves']
    elif 'device' in interface:
        devices = [interface['device']]
    return devices


class FilterModule(object):
    ''' ursula utility filters '''

    def filters(self):
        return {
            'ursula_controller_ips':    ursula_controller_ips,
            'ursula_memcache_hosts':    ursula_memcache_hosts,
            'ursula_package_path':      ursula_package_path,
            'remove_vlan_tag':          remove_vlan_tag,
            'net_physical_devices':     net_physical_devices,
        }
