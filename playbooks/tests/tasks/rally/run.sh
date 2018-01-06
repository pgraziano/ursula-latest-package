#!/bin/bash -xe
HELP() {
    echo "Usage: ./`basename $0` -e <cinder_enabled> -t <build_tag>"
    exit 1
}
while getopts 'e:t:h' OPT; do
    case $OPT in
        e)
            CINDER_ENABLED="$OPTARG";;
        t)
            BUILD_TAG="$OPTARG";;
        h)
            HELP;;
        ?)
            echo "Unknown argument!"
            HELP;;
    esac
done

source /root/stackrc

install_rally() {
    attempt=1
    until [[ $attempt == ${RALLY_MAX_RETRY} ]]; do
        curl -O ${RALLY_INSTALL_URL};chmod +x install_rally.sh; ./install_rally.sh -y -d rally
        if [[ -d rally ]]; then
            break
        else
            attempt=$[$attempt + 1]
            sleep ${RALLY_RETRY_SLEEP}
        fi
    done

    if [[ ! -d rally ]]; then
        echo "Could not install rally.  Check your connection?"
        exit 1
    fi
}

CINDER_ENABLED=${CINDER_ENABLED:-False}
BUILD_TAG=${BUILD_TAG:-master}
RALLY=rally/bin/rally
RALLY_INSTALL_URL=https://raw.githubusercontent.com/openstack/rally/master/install_rally.sh
RALLY_FILE=bbc-cloud-validate
RALLY_TEST_IMAGE="cirros"
RALLY_TEST_NET_ID=$(nova network-list | awk '/internal/{print $2}')
RALLY_TEST_VCPU_LIMIT=4
RALLY_MAX_RETRY=4
RALLY_RETRY_SLEEP=5

install_rally

cat << EOF > rally_args.yaml
---
image_name: ${RALLY_TEST_IMAGE}
net_id: ${RALLY_TEST_NET_ID}
vcpu_limit: ${RALLY_TEST_VCPU_LIMIT}
EOF

${RALLY} deployment create --fromenv --name=${BUILD_TAG}
${RALLY} task start bbc-cloud-validate.yml --task-args-file rally_args.yaml
if [[ ${CINDER_ENABLED} == "True" ]]; then
    ${RALLY} task start bbc-cloud-validate-ceph.yml --task-args-file rally_args.yaml
fi
${RALLY} task report --out=rally_report.html
