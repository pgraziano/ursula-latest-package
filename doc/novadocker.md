Nova Docker Support
===================

If you want to bootstrap a cloud with nova-docker installed, you can do the following:

Environment
-----------

Add the following to `envs/example/group_vars/compute` to to use the nova docker driver only on compute nodes, otherwise add it to `envs/example/defaults.yml` for all nodes.

```
glance:
  container_formats: ami,ari,aki,bare,ovf,docker
nova:
  compute_driver: novadocker.virt.docker.DockerDriver
```

Then use `ursula` to boot your openstack cluster just as you would normally.

Images
------

Adding docker images is currently something only an Administrator should do.   It's quite easy (the glance name should be the same as the docker image name):

```
$ export IMAGE=tutum/wordpress
$ docker pull $IMAGE && \
    docker save $IMAGE | \
    glance image-create --is-public=True --container-format=docker \
    --disk-format=raw --name $IMAGE
```

Then you should be able to boot a docker container like this:

```
$ nova boot --image=$IMAGE --flavor=1 --nic net-id=<net-uuid> my_first_docker
```

within just a few seconds the container will be up and running.

```
$ docker ps
$ curl <ip.of.docker.instance>
WORDPRESS SETUP PAGE
```
