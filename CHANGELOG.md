# Ursula Changelog

# 0.9.3

- system: avoid excessive apt updates
- db: fix arbitrator for recent Percona packages
- db: remove anonymous users
- installation: bootstrap playbook
- monitoring: improve RabbitMQ check
- monitoring: improve RAID check
- testenv: allow network to be specified

# 0.9.2

- system: disable swap
- system: update OpenSSL
- system: enable UFW firewall on all nodes
- haproxy: disable keepalives to fix Horizon issue
- testenv: use QEMU rather than nested KVM
- nova: setup SSH credentials for VM migrations
- nova: enable CPU core filter in scheduler
- keystone: only remove tokens over 24 hours old
- heat: do not add startup script or haproxy config when disabled
- mysql: increase maximum connections

# 0.9.1

- apt repositories: specify key id
- barbican, cinder, glance, neutron, nova: use HTTPS to connect to Keystone
- python: install pip 1.4.1
- add retry logic to git clones and pip installs
- mysql: move configuration to conf.d files
- testenv: use apt-proxy for initial dist-upgrade
- defaults: use internal floating IP for MySQL and RabbitMQ

# 0.9.0

- sensu_process_check now accepts parameters for warn overs
- sensu: monitor mylsqd on controllers
- sensu: monitor ipchanged
- kernel and tcp tuning
- ucarp to provide Neutron and Swift HA
- sensu_check: ensure occurences and interval are integers
- sensu_process: ensure bools are bools with check json
- swift fixups
- swift-dispersion checks into one check
- monitor that ntpd is running
- increase ansible fork config option to 25
- support neutron subnet allocation pools
- configure neutron to use non-admin keystone port
- ipmitool

# 0.8.5

- correctly set vxlan tunnel to be disabled
- raidset sensu check against 3ware cards
- lbaas feature flag (off by default)
- heat feature flag (off by default)
- keystone tokens will expire in 24hours by default
- use a git mirror

## 0.8.0

- Neutron LBaaS
- Swift
- initial VXLAN support
- store keystone tokens in mysql
- backup mysql db to local disk
- added vagrant support
- use UFW to manage firewall rules
- Ubuntu 14.04 LTS undercloud support
- HAProxy - prefer services on local controller
- allow for cinder.volume_clear_size
- reserve 4GB of RAM on controllers
- fix broken memcached sensus checks
- Monitor ntp offset

## 0.6.0

- percona refactor
- iptables lockdown
- install sensu certs to encrypt all sensu traffic

## 0.5.0

- simplified OpenStack API monitoring
- rabbitmq clustering (disabled by default)
- rabbitmq monitoring
- use system users for OpenStack services
- Barbican Support
- add stages to the ursula command
- Monitoring additions ( memcached, iscsid )
- mysql tuning

## 0.2.1

- Corrected memcached listen address
- Corrected horizon memcached config
- Fixed sensu-client OOO on fresh install

## 0.2.0

- Disabled nova conductor service
- Added system tools to common
- Added Ansible integration testing
- API HTTP checks
- Force UTC time
- Conditionally set OS_CACERT
- Sensu client enabled at boot
- Percona: specify the db arbiter host
- Percona montitoring: alert if not enough nodes in cluster
- DRY up log scanning
- Dashboard to use shared memcached servers vs local

## 0.1.0 and 0.1.1

- Initial release
