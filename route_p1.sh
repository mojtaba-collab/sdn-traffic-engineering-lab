

#!/usr/bin/env bash
set -euo pipefail

OF_VER="OpenFlow13"
PRIORITY=100
SWITCHES=(s1 s2 s3 s4 s5 s6)

echo "Flushing flow tables on all switches: ${SWITCHES[*]}..."
for sw in "${SWITCHES[@]}"; do
    sudo ovs-ofctl -O "$OF_VER" del-flows "$sw"
    sudo ovs-ofctl -O "$OF_VER" del-groups "$sw" 2>/dev/null || true
done

add_route() {
    local sw="$1"
    local ip="$2"
    local out_port="$3"
    # Forward ARP
    sudo ovs-ofctl -O "$OF_VER" add-flow "$sw" \
        "priority=$PRIORITY,arp,arp_tpa=$ip,actions=output:$out_port"
    # Forward IPv4
    sudo ovs-ofctl -O "$OF_VER" add-flow "$sw" \
        "priority=$PRIORITY,ip,nw_dst=$ip,actions=output:$out_port"
}

echo "Installing Path p1 (H1 <-> H4) and Path p2 (H2 <-> H3) rules..."

# --- Switch s1 ---
# Port 1: h1 | Port 2: s2
add_route s1 "10.0.0.1" 1
add_route s1 "10.0.0.4" 2

# --- Switch s2 ---
# Port 1: h2 | Port 2: s1 | Port 3: s3
# p1 traffic:
add_route s2 "10.0.0.1" 2
add_route s2 "10.0.0.4" 3
# p2 traffic:
add_route s2 "10.0.0.2" 1
add_route s2 "10.0.0.3" 3

# --- Switch s3 ---
# Port 1: h3 | Port 2: s2 | Port 3: s4
# p1 traffic:
add_route s3 "10.0.0.1" 2
add_route s3 "10.0.0.4" 3
# p2 traffic:
add_route s3 "10.0.0.2" 2
add_route s3 "10.0.0.3" 1

# --- Switch s4 ---
# Port 1: h4 | Port 2: s3
add_route s4 "10.0.0.1" 2
add_route s4 "10.0.0.4" 1

echo "Path p1 and Path p2 installed successfully."