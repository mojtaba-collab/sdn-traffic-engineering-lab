


#!/usr/bin/env python3
"""
Plot 3 Dynamic Redirection Benchmark:
Maintains lambda*_14 ~ 5 Mbps, injects cross-traffic lambda_23 (h2 -> h3),
detects when latency doubles, dynamically invokes route_p3.sh, and plots timeline.
"""

import argparse
import csv
import os
import re
import subprocess
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def parse_ping_rtt(output):
    match = re.search(r"time=([\d\.]+)\s*ms", output)
    return float(match.group(1)) if match else None


def get_host_pid(host_name: str):
    commands = [
        f"ps -ef | grep 'bash.*mininet:{host_name}' | grep -v grep | awk '{{print $2}}'",
        f"pgrep -f 'mininet:{host_name}'",
    ]
    for cmd in commands:
        try:
            output = subprocess.check_output(cmd, shell=True, text=True).strip().splitlines()
            if output and output[0].isdigit():
                return int(output[0])
        except subprocess.SubprocessError:
            continue
    return None


def run_in_host(pid: int, command: list, bg: bool = False):
    exec_cmd = ["sudo", "mnexec", "-a", str(pid)] + command
    if bg:
        return subprocess.Popen(exec_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return subprocess.run(exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def main():
    h1_pid = get_host_pid("h1")
    h2_pid = get_host_pid("h2")
    h3_pid = get_host_pid("h3")
    h4_pid = get_host_pid("h4")

    if not all([h1_pid, h2_pid, h3_pid, h4_pid]):
        print("Error: Could not locate PIDs for all Mininet hosts (h1-h4).", file=sys.stderr)
        sys.exit(1)

    timestamps = []
    latencies = []
    reroute_time = None

    try:
        subprocess.run(["sudo", "pkill", "-f", "iperf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

        # 1. Start iperf servers on h4 and h3
        run_in_host(h4_pid, ["iperf", "-s", "-u", "-p", "5001"], bg=True)
        run_in_host(h3_pid, ["iperf", "-s", "-u", "-p", "5002"], bg=True)
        time.sleep(1)

        # 2. Start constant stream lambda*_14 = 5 Mbps (50% utilization)
        print("Starting constant flow lambda*_14 = 5 Mbps (H1 -> H4)...")
        run_in_host(h1_pid, ["iperf", "-c", "10.0.0.4", "-u", "-b", "5M", "-t", "60", "-p", "5001"], bg=True)
        time.sleep(2)

        # Measure baseline latency
        baseline_samples = []
        for _ in range(5):
            res = run_in_host(h1_pid, ["ping", "-c", "1", "-W", "1", "10.0.0.4"])
            rtt = parse_ping_rtt(res.stdout)
            if rtt:
                baseline_samples.append(rtt)
            time.sleep(0.5)

        baseline_rtt = sum(baseline_samples) / len(baseline_samples) if baseline_samples else 40.0
        threshold_rtt = baseline_rtt * 2.0
        print(f"Baseline RTT: {baseline_rtt:.2f} ms | Redirection Trigger Threshold: {threshold_rtt:.2f} ms")

        # 3. Main Timeline Loop (30 seconds)
        h2_proc = None
        rerouted = False
        start_time = time.time()

        for step in range(30):
            current_t = time.time() - start_time

            # At t = 8s, start cross traffic h2 -> h3 to congest s2-s3 link
            if step == 8:
                print(">>> Injecting cross-traffic lambda_23 = 7 Mbps (H2 -> H3) to congest s2-s3 link...")
                h2_proc = run_in_host(h2_pid, ["iperf", "-c", "10.0.0.3", "-u", "-b", "7M", "-t", "30", "-p", "5002"], bg=True)

            # Probe latency h1 -> h4
            res = run_in_host(h1_pid, ["ping", "-c", "1", "-W", "1", "10.0.0.4"])
            rtt = parse_ping_rtt(res.stdout)

            timestamps.append(current_t)
            latencies.append(rtt)
            print(f"t={current_t:4.1f}s | Measured RTT: {rtt if rtt else 'DROP'} ms")

            # Check if latency doubled and reroute dynamically
            if not rerouted and step > 8 and rtt and rtt >= threshold_rtt:
                print(f">>> Latency exceeded threshold ({rtt:.2f} ms >= {threshold_rtt:.2f} ms)!")
                print(">>> Controller dynamically executing route_p3.sh to reroute onto path p3...")
                subprocess.run(["bash", "route_p3.sh"])
                rerouted = True
                reroute_time = current_t

            time.sleep(1)

    finally:
        subprocess.run(["sudo", "pkill", "-f", "iperf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Save Plot 3 Timeline
    plt.figure(figsize=(10, 5))
    valid_pts = [(t, l) for t, l in zip(timestamps, latencies) if l is not None]
    if valid_pts:
        tx, ty = zip(*valid_pts)
        plt.plot(tx, ty, marker="o", linestyle="-", color="#1976d2", label="H1-H4 Perceived Latency")

    plt.axhline(y=baseline_rtt, color="green", linestyle=":", label=f"Baseline Latency ({baseline_rtt:.1f} ms)")
    plt.axhline(y=threshold_rtt, color="orange", linestyle="--", label=f"Doubling Threshold ({threshold_rtt:.1f} ms)")

    if reroute_time:
        plt.axvline(x=reroute_time, color="red", linestyle="-.", label=f"Dynamic Reroute to p3 (t={reroute_time:.1f}s)")

    plt.title("Plot 3: Dynamic Redirection Timeline Under Cross-Traffic Congestion", fontsize=12)
    plt.xlabel("Timeline (seconds)", fontsize=11)
    plt.ylabel("Perceived End-to-End Latency (ms)", fontsize=11)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig("plot3_dynamic_timeline.png", dpi=300)
    print("Plot 3 timeline saved to plot3_dynamic_timeline.png")


if __name__ == "__main__":
    main()