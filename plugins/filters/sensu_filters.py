

def sensu_dependencies(check_name, hostvars, host_groups, check_groups):
    deps = set()
    check_groups = check_groups.split(',')
    for group in check_groups:
        if not group in host_groups:
            continue
        for host in host_groups[group]:
            client_name = '{}.{}-{}'.format(host, hostvars[host]['ansible_domain'], hostvars[host]['stack_env'])
            if 'monitoring' in hostvars[host]:
                if 'client_name' in hostvars[host]['monitoring']:
                    client_name = hostvars[host]['monitoring']['client_name']
            deps.add("{}/{}".format(client_name, check_name))
    return sorted(list(deps))


class FilterModule(object):
    ''' sensu utility filters '''

    def filters(self):
        return {
            'sensu_dependencies':    sensu_dependencies,
        }
