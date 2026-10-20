# Cache Pollution & Dynamic Path Redirection in OpenFlow Networks

This repository contains Mininet topology scripts, OpenFlow 1.3 flow-table configuration tools, and automated Python benchmarking suites used to evaluate end-to-end round-trip latency, Open vSwitch (OVS) software classifier lookup degradation under flow-table saturation attacks, and autonomous threshold-triggered dynamic path redirection under link congestion.

---

## Network Architecture & Topologies

The testbed uses a 6-switch SDN topology (`s1` through `s6`) connecting four hosts (`h1` to `h4`) with uniform link constraints:
- **Link Bandwidth (B):** 10.0 Mbps
- **Propagation Delay (d):** 5.0 ms per link
- **Queue Limit (q):** 100 packets

### Forwarding Path Matrix

| Path Designation | Endpoints & Role | Switch Sequence | Links / Theoretical Minimum RTT |
| :--- | :--- | :--- | :--- |
| **Path p1** | H1 <-> H4 (Primary) | h1 <-> s1 <-> s2 <-> s3 <-> s4 <-> h4 | 5 links (4 switches) -> 50.0 ms |
| **Path p2** | H2 <-> H3 (Cross-Traffic) | h2 <-> s2 <-> s3 <-> h3 | 3 links (2 switches) -> 30.0 ms |
| **Path p3** | H1 <-> H4 (Bypass) | h1 <-> s1 <-> s5 <-> s6 <-> s4 <-> h4 | 5 links (4 switches) -> 50.0 ms |

---

## Experimental Phases

### Phase 1: Baseline Bottleneck Latency (Plot 1)
- Sweeps UDP traffic injection rates (lambda_14) from 1.0 Mbps to 9.6 Mbps along Path p1.
- Tracks baseline propagation delay (50.3 - 50.5 ms) and queue saturation knee dynamics (150.3 ms at 9.6 Mbps).

### Phase 2: Flow-Table Pollution Attack (Plot 2)
- Populates ingress switch `s1` with 3,000+ wildcard OpenFlow rules across destination Layer-4 ports (1000–4000).
- Uses dynamic UDP probes to induce a 100% miss rate in the OVS Exact Match Cache (EMC), forcing userspace classifier evaluations and producing a steady +6.35 ms lookup penalty.

### Phase 3: Dynamic Congestion Rerouting (Plot 3)
- Maintains a continuous 5.0 Mbps stream on Path p1 (H1 -> H4).
- Injects 7.0 Mbps cross-traffic on Path p2 (H2 -> H3), overloading the shared s2-s3 link (12.0 Mbps > 10.0 Mbps) and spiking latency to 166.0 ms.
- Detects when latency doubles (>= 102.64 ms) and automatically executes `route_p3.sh` to install high-priority rules (priority=200), restoring latency to ~51.4 ms.

---



## Repository Structure

```text
├── README.md                                           # Repository overview, architecture, and reproduction steps
├── SDN Flow Table Saturation and Dynamic Rerouting.pdf # Formal experimental lab report
├── complete_path.jpeg                                  # SDN topology and routing paths diagram
├── project_topo.py                                     # Mininet 6-switch, 4-host network topology setup
├── route_p1.sh                                         # Baseline flow installation script (Path p1 & Path p2)
├── route_p3.sh                                         # High-priority dynamic reroute script (Path p3)
├── inject_cache_pollution.py                           # Flow-table saturation attack tool (3,000+ wildcard rules)
├── bench_baseline_latency.py                           # Phase 1 forward and reverse rate-sweep harness
├── bench_table_saturation.py                           # Phase 2 dynamic probe table saturation harness
├── bench_dynamic_reroute_plot3.py                      # Phase 3 real-time monitoring and reroute controller
├── plot1_data.csv                                      # Phase 1 forward baseline latency measurements
├── plot1_latency_vs_rate.png                           # Phase 1 forward baseline latency plot
├── plot1_reverse_data.csv                              # Phase 1 reverse baseline latency measurements
├── plot1_reverse_latency.png                           # Phase 1 reverse baseline latency plot
├── plot2_data.csv                                      # Phase 2 flow-table pollution measurements
├── plot2_cache_pollution.png                           # Phase 2 classifier lookup penalty comparison plot
├── plot3_dynamic_timeline.png                          # Phase 3 dynamic rerouting timeline plot

```

---

## Step-by-Step Reproduction Guide

### Prerequisites

* Ubuntu 20.04 / 22.04 LTS
* Mininet 2.3.0+
* Open vSwitch 2.17.0+
* Python 3.8+ with `matplotlib`

```bash
sudo apt-get update
sudo apt-get install -y mininet openvswitch-switch iperf python3-matplotlib

```

### Execution Steps

#### 1. Clean Environment

Terminate any lingering `iperf` or Mininet instances:

```bash
sudo pkill -9 -f iperf
sudo mn -c

```

#### 2. Phase 1: Baseline Benchmark (Plot 1)

* **Terminal 1** (Launch Mininet):
```bash
sudo python3 project_topo.py

```


* **Terminal 2** (Run Benchmark):
```bash
sudo bash route_p1.sh
python3 bench_baseline_latency.py
python3 bench_baseline_latency.py --reverse

```



#### 3. Phase 2: Flow-Table Pollution Attack (Plot 2)

In **Terminal 2**:

```bash
# Inject 3,000+ attack rules into ingress switch s1
python3 inject_cache_pollution.py -n 4000

# Verify switch flow count
sudo ovs-ofctl -O OpenFlow13 dump-flows s1 | wc -l

# Run saturation benchmark with dynamic port probes
python3 bench_table_saturation.py

```

#### 4. Phase 3: Dynamic Congestion Rerouting (Plot 3)

In **Terminal 2**:

```bash
# Flush attack rules and restore clean baseline
sudo bash route_p1.sh

# Run real-time monitoring and dynamic redirection
python3 bench_dynamic_reroute_plot3.py

```

---

## Experimental Results

| Phase | Scenario | Observed Latency | Network State |
| --- | --- | --- | --- |
| **Phase 1** | Baseline Sweep ($1.0\text{--}9.0\text{ Mbps}$) | $50.30\text{--}50.57\text{ ms}$ | Physical propagation delay |
| **Phase 1** | Bottleneck Saturation ($9.6\text{ Mbps}$) | $150.30\text{ ms}$ | Queue buffer accumulation ($q \approx 95$) |
| **Phase 2** | Table Pollution ($1.0\text{--}9.0\text{ Mbps}$) | $56.43\text{--}56.92\text{ ms}$ | $+6.35\text{ ms}$ userspace classifier overhead |
| **Phase 3** | Cross-Traffic Congestion ($t=9.8\text{s}$) | $166.00\text{ ms}$ | Link buffer overflow on $s2\text{--}s3$ |
| **Phase 3** | Post-Reroute Recovery ($t > 11.5\text{s}$) | $50.60\text{--}51.90\text{ ms}$ | Clean transmission across Path $p_3$ |

```

```
