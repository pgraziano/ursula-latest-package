#!/bin/bash -xe
# This script is run from Jenkins jobs to execute setup/deploy/test/rally steps
# in Ursula with different test environments and installation methods
HELP() {
    echo "Usage: ./`basename $0` -t <test_env> -m <install_method: source|package|distro>"
    echo "-i <image_id> -u <login_user> -v <openstack_package_version> -e <extra_vars> -h <help>"
    exit 1
}
while getopts 't:m:i:u:v:e:h' OPT; do
    case $OPT in
        t)
            TEST_ENV="$OPTARG";;
        m)
            INSTALL_METHOD="$OPTARG";;
        i)
            IMAGE_ID="$OPTARG";;
        u)
            LOGIN_USER="$OPTARG";;
        v)
            PACKAGE_VERSION="$OPTARG";;
        e)
            EXTRA_VARS="$OPTARG";;
        h)
            HELP;;
        ?)
            echo "Unknown argument!"
            HELP;;
    esac
done

if [[ -z ${PACKAGE_VERSION} && "${INSTALL_METHOD}" == "package" ]]; then
    echo "openstack_package_version is not specified!"
    exit 1
fi

export STACK_RC=~/jenkins.stackrc
export CI=jenkins
export PATH=${WORKSPACE}/venv/bin:$PATH
export TEST_ENV=${TEST_ENV:-ci-full-ubuntu}
export INSTALL_METHOD=${INSTALL_METHOD:-source}
export IMAGE_ID=${IMAGE_ID:-ci-trusty}
export LOGIN_USER=${LOGIN_USER:-ubuntu}

function cleanup {
    set +e
    if [[ "${INSTALL_METHOD}" == "distro" ]]; then
        test/run rhn_unsubscribe
    fi
    test/cleanup
    ssh-agent -k
}

trap cleanup EXIT TERM
eval $(ssh-agent -s -t 14400)
ssh-add -D
test/setup ${EXTRA_VARS}
pip install pyopenssl ndg-httpsclient pyasn1
sleep 120
if [[ "${INSTALL_METHOD}" == "package" ]]; then
    echo "openstack_install_method: '${INSTALL_METHOD}'" >> envs/example/test/group_vars/all.yml
    echo "openstack_package_version: '${PACKAGE_VERSION}'" >> envs/example/test/group_vars/all.yml
fi
test/run deploy ${EXTRA_VARS}
test/run test
test/run rally --extra-vars "build_tag=${BUILD_TAG} workspace=${WORKSPACE}"
