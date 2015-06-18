#!/bin/bash

# Launch Kubernetes on CoreOS
EXE_DIR=$(dirname $0)
source ${EXE_DIR}/global.conf
MASTER_IP=${1:-172.17.8.101}

function get_host_os {
    # Detect the OS name/arch so that we can find our binary
    case "$(uname -s)" in
        Darwin)
            host_os=darwin
            ;;
        Linux)
            host_os=linux
            ;;
        *)
            echo "Unsupported host OS.  Must be Linux or Mac OS X." >&2
            exit 1
            ;;
    esac

    echo $host_os
}

function get_host_arch {
    case "$(uname -m)" in
    x86_64*)
        host_arch=amd64
        ;;
    i?86_64*)
        host_arch=amd64
        ;;
    amd64*)
        host_arch=amd64
        ;;
    arm*)
        host_arch=arm
        ;;
    i?86*)
        host_arch=x86
        ;;
    *)
        echo "Unsupported host arch. Must be x86_64, 386 or arm." >&2
        exit 1
        ;;
    esac
    
    echo $host_arch
}
               

function install_kubectl {

    echo "Downloading kubectl"
    wget -O ${EXE_DIR}/kubectl https://storage.googleapis.com/kubernetes-release/release/${KUBERNETES_VERSION}/bin/${HOST_OS}/${HOST_ARCH}/kubectl
    chmod +x ${EXE_DIR}/kubectl
}

function install_fleetctl {

    echo "Downloading fleetctl"
    
    if [ "$HOST_OS" = "darwin" ]; then
        ZIP_OR_TGZ="zip"
    else
        ZIP_OR_TGZ="tar.gz"
    fi
    
    wget -O /tmp/fleet.$ZIP_OR_TGZ  https://github.com/coreos/fleet/releases/download/${FLEET_VERSION}/fleet-${FLEET_VERSION}-${HOST_OS}-${HOST_ARCH}.$ZIP_OR_TGZ
    pushd /tmp

    if [ "$ZIP_OR_TGZ" = "zip" ]; then
        unzip fleet.$ZIP_OR_TGZ
    else
        tar zxf fleet.$ZIP_OR_TGZ
    fi
    popd

    cp /tmp/fleet-${FLEET_VERSION}-${HOST_OS}-${HOST_ARCH}/fleetctl ${EXE_DIR}/
    chmod +x ${EXE_DIR}/fleetctl
    rm -rf /tmp/fleet.$ZIP_OR_TGZ /tmp/fleet-${FLEET_VERSION}-${HOST_OS}-${HOST_ARCH}/
}

HOST_OS=$(get_host_os)
HOST_ARCH=$(get_host_arch)

if [ ! -f ${EXE_DIR}/fleetctl ]; then
    install_fleetctl
fi

if [ ! -f kubectl ]; then
    install_kubectl
fi

export FLEETCTL_ENDPOINT=http://${MASTER_IP}:2379

# Make sure we're using the right Kubernetes version as set in global.conf
sed "s|__KUBERNETES_VERSION__|${KUBERNETES_VERSION}|g;" ${EXE_DIR}/units/kube-install.service.in > ${EXE_DIR}/units/kube-install.service

SERVICES="kube-install kube-apiserver kube-controller-manager kube-scheduler kubelet kube-proxy kube-proxy-master kube-addons"

for service in ${SERVICES}; do
    ${EXE_DIR}/fleetctl destroy ${service}.service > /dev/null
done
for service in ${SERVICES}; do
    ${EXE_DIR}/fleetctl submit ${EXE_DIR}/units/${service}.service
    ${EXE_DIR}/fleetctl start ${EXE_DIR}/units/${service}.service
done
