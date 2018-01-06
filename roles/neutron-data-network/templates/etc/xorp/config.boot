interfaces {
    restore-original-config-on-shutdown: false
    interface {{ hostvars[inventory_hostname][neutron.vxlan_interface|default(primary_interface)]['device'] }} {
        description: "Internal pNodes interface"
        disable: false
        default-system-config
    }
}

protocols {
    igmp {
        disable: false
        interface {{ hostvars[inventory_hostname][neutron.vxlan_interface|default(primary_interface)]['device'] }} {
            vif {{ hostvars[inventory_hostname][neutron.vxlan_interface|default(primary_interface)]['device'] }} {
                disable: false
                version: 3
            }
        }
        traceoptions {
            flag all {
                disable: false
            }
        }
    }
}
