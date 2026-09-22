#!/usr/bin/env bash

templateid=$1
vmid=$2
vmip=$3
vmname=$4

qm clone $templateid $vmid --name $vmname --full
qm set $vmid --ipconfig0 ip=10.10.10.${vmip}/24,gw=10.10.10.1
qm set $vmid --nameserver "10.212.226.10 10.212.226.11"
qm set $vmid --ciuser ansible
qm set $vmid --sshkey ansible_id_ed25519.pub

