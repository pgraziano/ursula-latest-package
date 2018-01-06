# How to set up a dev/test environment

NOTE: Ursula comes setup for Vagrant to complete dev/test work within.  Please see the [Ursula Vagrant](https://github.com/blueboxgroup/ursula/blob/master/doc/dev-test.md#vagrant) instructions for more details.

Ursula also comes with scripts to automatically spin up a test environment inside of openstack vms (OpenStack on OpenStack).

## First-time workstation setup

Confirm that you have followed the [installation instructions for ursula](https://github.com/blueboxgroup/ursula#installation).

## Vagrant Support

Vagrant support is built in. To get started, run:

```
$ ursula --provisioner=vagrant envs/example/allinone site.yml
```

## Unit tests

You can invoke `tox` to run unit tests ( currently `pep8` and `ansible` in test mode. ) in a virtual environment.

```bash
    $ tox
```

You can also run the tests outside of a virtual env like so:

```bash
    $ pep8 --show-source --show-pep8 .
    $ ursula -t -e envs/example -p site.yml
```

### Spin up a new environment

```bash
    $ ./test/setup       # boot vms and write an ansible inventory to envs/example/hosts
    $ ./test/run         # run site.yml and run all the tests
```

### Iterate on an existing environment

You can save time on iterating by keeping your vms around for multiple ansible runs.

```bash
    $ ./test/run         # re-run site.yml (much faster this time)
```

### Re-run only a subset of tasks

    TODO

### Throw away the vms when you're done

```bash
    $ ./test/cleanup     # delete vms
```

## DockerDockerDockerDockerDockerDocker (Unsupported)

If you're feeling a little frisky, you can deploy a test/dev environment straight from our docker images.
This will run `test/deploy && test/run` from inside the container and use the stackrc file that you've mapped in:

```
$ docker run -ti -v /path/to/.stackrc:/root/.stackrc  bluebox/ursula
writing initial inventory file
destroying: test-controller-0 test-controller-1 test-compute-0

PLAY [de-provision test instances] ********************************************
Friday 21 November 2014  02:43:42 +0000 (0:00:00.021)       0:00:00.021 *******
===============================================================================

GATHERING FACTS ***************************************************************
Friday 21 November 2014  02:43:42 +0000 (0:00:00.000)       0:00:00.021 *******
ok: [127.0.0.1]
...
...
```
