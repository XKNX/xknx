#!/bin/bash

if [[ -f .config ]]; then
    source .config
else
    echo "Please create the .config file containing the HA_UPSTREAM and the XKNX_REPO variables"
    exit 1
fi

if [[ ! -d ${XKNX_REPO}/home-assistant-plugin ]]; then
    echo "XKNX repo path is wrong"
    exit 1
fi

if [[ ! -d ${HA_UPSTREAM}/homeassistant ]]; then
    echo "HA upstream repo path is wrong"
    exit 1
fi

export RELEASE=`curl --silent "https://api.github.com/repos/XKNX/xknx/releases/latest" | python -c 'import json, sys; print(json.loads(sys.stdin.read())["tag_name"]);'`

currentKernel="$(uname -s)"
case "${currentKernel}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    *)          machine="UNKNOWN:${currentKernel}"
esac

if [ "$machine" != "Linux" ] && [ "$machine" != "Mac" ]; then
    echo "This script is only supported for Mac and Linux environments. Exiting therefore."
    exit 1
fi

export MACHINE=${machine}

###
# $1 pattern
# $2 target
###
function replace_values() {
    if [ "$MACHINE" == "Linux" ];
    then
        sed -i "$1" "$2"
    else
        sed -i '.bak' "$1" "$2"
    fi
}