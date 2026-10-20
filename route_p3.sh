


#!/usr/bin/env bash
set -euo pipefail

OF_VER="OpenFlow13"
PRIORITY=200

echo "Rerouting H1 <-> H4 onto Path p3 (s1 -> s5 -> s6 -> s4)..."

# --- Transit Switches s5 & s6 ---
# s5: Port 1 -> s1, Port 2 -> s6
sudo ovs-ofctl -O "$OF_VER" add-flow s5 "priority=$PRIORITY,ip,nw_dst=10.0.0.4,actions=output:2"
sudo ovs-ofctl -O "$OF_VER" add-flow s5 "priority=$PRIORITY,ip,nw_dst=10.0.0.1,actions=output:1"
sudo ovs-ofctl -O "$OF_VER" add-flow s5 "priority=$PRIORITY,arp,arp_tpa=10.0.0.4,actions=output:2"
sudo ovs-ofctl -O "$OF_VER" add-flow s5 "priority=$PRIORITY,arp,arp_tpa=10.0.0.1,actions=output:1"

# s6: Port 1 -> s5, Port 2 -> s4
sudo ovs-ofctl -O "$OF_VER" add-flow s6 "priority=$PRIORITY,ip,nw_dst=10.0.0.4,actions=output:2"
sudo ovs-ofctl -O "$OF_VER" add-flow s6 "priority=$PRIORITY,ip,nw_dst=10.0.0.1,actions=output:1"
sudo ovs-ofctl -O "$OF_VER" add-flow s6 "priority=$PRIORITY,arp,arp_tpa=10.0.0.4,actions=output:2"
sudo ovs-ofctl -O "$OF_VER" add-flow s6 "priority=$PRIORITY,arp,arp_tpa=10.0.0.1,actions=output:1"

# --- Update Edge Switches s1 & s4 with higher priority rules ---
# s1: Send traffic for h4 out Port 3 (toward s5) instead of Port 2
sudo ovs-ofctl -O "$OF_VER" add-flow s1 "priority=$PRIORITY,ip,nw_dst=10.0.0.4,actions=output:3"
sudo ovs-ofctl -O "$OF_VER" add-flow s1 "priority=$PRIORITY,arp,arp_tpa=10.0.0.4,actions=output:3"
# Return traffic arriving from s5 (Port 3) to h1 (Port 1)
sudo ovs-ofctl -O "$OF_VER" add-flow s1 "priority=$PRIORITY,in_port=3,ip,nw_dst=10.0.0.1,actions=output:1"
sudo ovs-ofctl -O "$OF_VER" add-flow s1 "priority=$PRIORITY,in_port=3,arp,arp_tpa=10.0.0.1,actions=output:1"

# s4: Send traffic for h1 out Port 3 (toward s6) instead of Port 2
sudo ovs-ofctl -O "$OF_VER" add-flow s4 "priority=$PRIORITY,ip,nw_dst=10.0.0.1,actions=output:3"
sudo ovs-ofctl -O "$OF_VER" add-flow s4 "priority=$PRIORITY,arp,arp_tpa=10.0.0.1,actions=output:3"
# Return traffic arriving from s6 (Port 3) to h4 (Port 1)
sudo ovs-ofctl -O "$OF_VER" add-flow s4 "priority=$PRIORITY,in_port=3,ip,nw_dst=10.0.0.4,actions=output:1"
sudo ovs-ofctl -O "$OF_VER" add-flow s4 "priority=$PRIORITY,in_port=3,arp,arp_tpa=10.0.0.4,actions=output:1"

echo "Path p3 activated successfully. Path p2 (H2 <-> H3) remains intact."