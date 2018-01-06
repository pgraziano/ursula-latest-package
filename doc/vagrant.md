Ursula on Vagrant
=================

Vagrant is an excellent tool for easily testing out new tools or systems without having to install a bunch of crap to your userland.

Prerequisites
==============

* Virtualbox
* Vagrant

Networking
==========

We've strived to keep the networking in the Vagrant install simple.  It _may_ not resemble what you would run in production,  but it does allow for an easier introduction to OpenStack.

There are four network interfaces provided in the Vagrantfile.

eth0
----

Vagrant guest IP:  This isn't of any interest to us.

eth1
----

Host Networking:  This is the primary network for the OpenStack hosts and services.

eth2
----

Instance _Private_ Networking:  This is a single flat provider network that allows your instances to share IPs on the same network and uses the VM provider's gateway for routing.   This means that you should be able to access your instances from the regular network without having to enter/exit network name spaces.

There are plans to also allow tenant networks via VLAN/VXLAN tunnels which would also exist across this interface.  This is not yet implemented.

eth3
----

Instance _Public/Floating IP_ Networking:  This interface is reserved for Floating IPs.   It is not currently being used but there are plans to enable floating IPs.

Using
=====

Vagrant can be used to stand up three types of environments:  allinone, standard, swift.

Do not use `vagrant up` directly.

Use `$ ursula --provisioner=vagrant envs/example/allinone site.yml`


allinone
--------

This will stand up a single monolithic OpenStack VM.  It's much quicker than standard, but sacrifices HA and multi-node:

```
$ ursula --provisioner=vagrant envs/example/allinone site.yml
$ vagrant ssh  allinone
$ vagrant destroy allinone
```

standard
--------

This will stand up two controllers and a compute node.  It includes all the appropriate HA pieces and is a fairly good facsimile of a production install:

```
$ ursula --provisioner=vagrant envs/example/standard site.yml
```

swift
-----

This will stand up a multi-node swift cluster:

```
$ ursula --provisioner=vagrant envs/example/swift site.yml
```
