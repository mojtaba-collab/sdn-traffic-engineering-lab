\# SDN Traffic Engineering \& Multipath Offloading



This repository contains Mininet topology scripts, OpenFlow 1.3 configuration tools, and automated benchmarking suites used to evaluate end-to-end RTT latency, software flow-table saturation attacks, path failover, and multipath offloading across a 6-switch SDN topology.



\## Experimental Phases \& Project Structure



1\. \*\*Phase 1: Baseline Latency\*\*

&#x20;  - `project\_topo` — 6-switch topology (`s1` through `s6`) with 10 Mbps link bandwidth and 100-packet buffer limits.

&#x20;  - `route\_p1.sh` — Installs full-mesh routing over Path 1 (`s1 -> s2 -> s3 -> s4`).

&#x20;  - `bench\_baseline\_latency` — Measures pristine baseline RTT and queue behavior under increasing UDP load rates.



2\. \*\*Phase 2: Flow-Table Pollution Attack\*\*

&#x20;  - `inject\_cache\_pollution` — Injects high-priority non-matching rules to stress the Open vSwitch software classifier and induce lookup penalties.

&#x20;  - `traffic\_polluter` — Background script generating randomized UDP microflows to evict kernel datapath entries.

&#x20;  - `bench\_table\_saturation` — Evaluates latency degradation and lookup penalties under switch saturation.



3\. \*\*Phase 3: Static Rerouting \& Path Failover\*\*

&#x20;  - `route\_p2.sh` — Migrates traffic to clean alternate Path 2 (`s1 -> s5 -> s6 -> s4`).

&#x20;  - `bench\_static\_reroute` — Measures RTT recovery and alternate link capacity bounds.



4\. \*\*Phase 4: Dynamic Multipath Offloading\*\*

&#x20;  - `route\_multipath` — Provisions OpenFlow 1.3 select groups for 50/50 traffic splitting across Path 1 and Path 2.

&#x20;  - `bench\_multipath\_offload` — Evaluates load distribution and latency mitigation under high aggregate rates.



\## Repository Layout



\### Scripts \& Topologies

\* `project\_topo` — Mininet network setup script

\* `route\_p1.sh` — Path 1 rule installation helper

\* `route\_p2.sh` — Path 2 rule installation helper

\* `route\_multipath` — OpenFlow 1.3 select group multipath configurator

\* `inject\_cache\_pollution` — Software flow-table stress tool

\* `traffic\_polluter` — Background UDP microflow generator

\* `bench\_baseline\_latency` — Phase 1 benchmark runner

\* `bench\_table\_saturation` — Phase 2 attack benchmark runner

\* `bench\_static\_reroute` — Phase 3 failover benchmark runner

\* `bench\_multipath\_offload` — Phase 4 multipath benchmark runner



\### Data \& Visualizations

\* `plot1\_data` \& `plot1\_latency\_vs\_rate` — Baseline RTT measurements and chart

\* `plot2\_data` \& `plot2\_cache\_pollution` — Flow-table pollution attack measurements and chart

\* `plot3\_data` \& `plot3\_path2\_latency` — Path 2 failover measurements and chart

\* `plot4\_data` \& `plot4\_multipath` — Multipath offloading measurements and chart

