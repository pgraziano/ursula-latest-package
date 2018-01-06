# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

NUM_CONTROLLERS = ENV['URSULA_NUM_CONTROLLERS'] || 2
NUM_COMPUTES = ENV['URSULA_NUM_COMPUTES'] || 1
NUM_SWIFT_NODES = ENV['URSULA_NUM_SWIFT_NODES'] || 3

if File.file?('.vagrant/vagrant.yml')
  SETTINGS_FILE = ENV['SETTINGS_FILE'] || '.vagrant/vagrant.yml'
else
  SETTINGS_FILE = ENV['SETTINGS_FILE'] || 'vagrant.yml'
end

require 'yaml'

SETTINGS = YAML.load_file SETTINGS_FILE

BOX_NAME = ENV['URSULA_BOX_NAME'] || SETTINGS['default']['box'] || 'ubuntu-trusty'
BOX_URL = ENV['URSULA_BOX_URL'] || SETTINGS['default']['box_url'] || 'http://opscode-vm-bento.s3.amazonaws.com/vagrant/virtualbox/opscode_ubuntu-14.04_chef-provisionerless.box'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = BOX_NAME
  config.vm.box_url = BOX_URL
  config.vm.provider "virtualbox" do |v|
    v.memory = SETTINGS['default']['memory']
    v.cpus = SETTINGS['default']['cpus']
    #v.gui = true
  end

  if Vagrant.has_plugin?('vagrant-openstack-provider')
    require 'vagrant-openstack-provider'
    config.vm.provider :openstack do |os, override|
      os.openstack_auth_url = "#{ENV['OS_AUTH_URL']}/tokens"
      os.username           = ENV['OS_USERNAME']
      os.password           = ENV['OS_PASSWORD']
      os.tenant_name        = ENV['OS_TENANT_NAME']
      os.flavor             = 'm1.small'
      os.image              = 'ubuntu-14.04'
      os.openstack_network_url = ENV['OS_NEUTRON_URL'] if ENV['OS_NEUTRON_URL']
      os.networks           =  ['internal']
      os.security_groups    = ['vagrant']
      os.floating_ip_pool   = 'external'
      override.vm.box       = 'openstack'
      override.ssh.username = 'ubuntu'
    end
  end

  config.ssh.forward_agent = true

  SETTINGS['vms'].each do |name, vm|
    config.vm.define name do |c|
      c.vm.hostname = "#{name}.ursula"
      if vm.has_key?('ip_address')
        if vm['ip_address'].kind_of?(Array)
          vm['ip_address'].each do |ip|
            c.vm.network :private_network, ip: ip
          end
        else
          c.vm.network :private_network, ip: vm['ip_address']
        end
      end
      if vm.has_key?('memory') || vm.has_key?('cpus')
        c.vm.provider "virtualbox" do |v|
          v.memory = vm['memory'] if vm.has_key?('memory')
          v.cpus = vm['cpus'] if vm.has_key?('cpus')
          if vm.has_key?('custom')
            if vm['custom'].kind_of?(Array)
              vm['custom'].each do |custom|
                v.customize eval(custom)
              end
            else
              v.customize eval(vm['custom'])
            end
          end
        end
        c.vm.provider "libvirt" do |v|
          v.memory = vm['memory'] if vm.has_key?('memory')
          v.cpus = vm['cpus'] if vm.has_key?('cpus')
	  if vm.has_key?('libvirt')
	    if vm['libvirt'].has_key?('storage')
		v.storage :file, vm['libvirt']['storage']
	    end
          end
          v.nested = true
        end

      end
    end
  end

end
