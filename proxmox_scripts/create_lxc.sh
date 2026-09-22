#!/usr/bin/env bash

templateid=debian-13-standard_13.6-1_amd64.tar.zst
vmid=$1
vmip=$2
vmname=$3

pct create $vmid local:vztmpl/${templateid} \
	    --hostname $vmname \
	        --ostype debian \
		    --unprivileged 1 \
		        --cores 2 \
			    --memory 2048 \
			        --swap 512 \
				    --rootfs raid-lvm:8 \
				        --net0 name=eth0,bridge=vmbr1,ip=10.10.10.${vmip}/24,gw=10.10.10.1 \
					    --nameserver "10.212.226.10 10.212.226.11" \
					        --onboot 1 \
						    --features nesting=1 \
						        --start 1

pct exec $vmid -- useradd -m -s /bin/bash ansible
pct exec $vmid -- mkdir -p /home/ansible/.ssh
pct push $vmid /root/ansible_id_ed25519.pub /home/ansible/.ssh/authorized_keys
pct exec $vmid -- chown -R ansible:ansible /home/ansible/.ssh
pct exec $vmid -- chmod 700 /home/ansible/.ssh
pct exec $vmid -- chmod 600 /home/ansible/.ssh/authorized_keys
pct exec $vmid -- apt-get update
pct exec $vmid -- apt-get install -y sudo
pct exec $vmid -- usermod -aG sudo ansible
pct exec $vmid -- sh -c 'echo "ansible ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ansible'
pct exec $vmid -- chmod 440 /etc/sudoers.d/ansible

