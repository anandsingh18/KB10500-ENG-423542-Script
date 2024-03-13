#!/usr/bin/env python
#
# Copyright (c) 2017 Nutanix Inc. All rights reserved.
#
#
# Disclaimer: Usage of this tool must be under guidance of Nutanix Support or an authorized partner
# Summary: Tool to read and manipulate acropolis address cache which stores the MAC-to-IP address mappings.
# Version of the script: Version 1
# Compatible software version(s): AHV versions prior to 
# Brief syntax usage:
#   python address_cache.py --list
#   python address_cache.py --get 0 11:ff:ff:ff:ff:ee
#   python address_cache.py --set 0 11:ff:ff:ff:ff:ee 192.168.0.2
#   python address_cache.py --del 0 11:ff:ff:ff:ff:ee
# Caveats: None
#
import os
VIRTUALENV_PATH = "/home/nutanix/.venvs/bin/bin/python3.9"
if os.path.exists(VIRTUALENV_PATH):
  if os.environ.get("PYTHON_TARGET_VERSION") is None:
    os.environ["PYTHON_TARGET_VERSION"] = "3.9"
  if os.environ.get("PYTHON_TARGET_PATH") is None:
    os.environ["PYTHON_TARGET_PATH"] = VIRTUALENV_PATH

import env
import gflags
from datetime import datetime
import time

from gevent import monkey
monkey.patch_all

from acropolis.common.interfaces import AcropolisInterfaces
from acropolis.net.address_cache import AcropolisNetworkAddressCache
from acropolis.utils import AcropolisUuid
from util.net.protocol.types import MacAddress, IPv4Address

gflags.FLAGS([])
gflags.FLAGS.logtostderr = True

interfaces = AcropolisInterfaces()

def print_syntax_and_exit(program_name):
  print("Usage:")
  print("%s \n\t--list\n\t--set <network-id> <mac> <ip>\n\t" \
        "--get <network-id> <mac>\n\t--del <network-id> <mac>]" % program_name)
  sys.exit(1)

def print_address_entry(address_entry):
  print("mac:", str(MacAddress(address_entry.mac_address)),\
         "network_id:", address_entry.network_id)
  for ip_entry in address_entry.ip_address_list:
    expiry = datetime.fromtimestamp(ip_entry.expiry_time_usecs/1e6).isoformat()
    last_seen = datetime.fromtimestamp(
        ip_entry.last_seen_time_usecs/1e6).isoformat()

  print("\tip:", str(IPv4Address(ip_entry.ip_address)), \
          "expiry:", expiry,\
          "last_seen", last_seen)

def main(args):
  if len(args) not in [2,4,5]:
    print_syntax_and_exit(args[0])

  cache = AcropolisNetworkAddressCache(interfaces)
  if args[1] == "--list":
    for address_entry in cache.iter_all():
      if not address_entry.deleted:
        print_address_entry(address_entry)
  else:
    network_id = int(args[2])
    mac = MacAddress.from_str(args[3]).bytes
    if args[1] == "--set":
      ip = IPv4Address.from_str(args[4]).bytes
      if not cache.set(network_id, mac, ip, 30):
        print("Set failed!")
    elif args[1] == "--del":
      if not cache.delete(network_id, mac):
        print("Delete failed!")
    elif args[1] == "--get":
      for (ip_address, last_seen_us) in cache.get([(network_id, mac)])[0]:
        last_seen = datetime.fromtimestamp(last_seen_us/1e6).isoformat()
        print(str(IPv4Address(ip_address)), last_seen)
    else:
      print_syntax_and_exit()

if __name__ == "__main__":
  import sys
  sys.exit(main(sys.argv))
