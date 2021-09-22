#!/bin/bash
#
# Shell script to setup a management server node.
# Notice that this is very lightweight.

sudo apt-get --assume-yes update
sudo apt-get --assume-yes install wireguard

sudo su
cd /etc/wireguard/
umask 077

# Genrate public and private keys for the VPN interface
wg genkey | tee privatekey | wg pubkey > publickey

# sudo su
# Copy data_platform/ai_stack_installer/vpn_mgmt.conf-server-reference to /etc/wireguard/vpn_mgmt.conf
# In vpn_mgmt.conf, replace PLACEHOLDER_REPLACE_WITH_GENERATED_KEY with generated privatekey
# exit 

sudo systemctl restart wg-quick@vpn_mgmt
sudo systemctl enable wg-quick@vpn_mgmt
