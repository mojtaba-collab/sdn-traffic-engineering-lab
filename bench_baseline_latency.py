



#!/usr/bin/env python3
"""
Benchmark Runner: End-to-End Latency vs. Injected Traffic Rate (Plot 1 & Bidirectional)
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

TRAFFIC_RATES = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 8.5, 9.0, 9.3, 9.6]


def parse_args():
    parser = argparse.ArgumentParser(description="Sweep traffic rates and measure latency.")
    parser.add_argument("--reverse", action="store_true", help="Run H4 -> H1 instead of H1 -> H4")
    parser.add_argument("--csv-out", default=None, help="CSV output filename")
    parser.add_argument("--plot-out", default=None, help="PNG plot output filename")
    parser.add_argument("--rates", nargs="+", type=float, default=TRAFFIC_RATES)
    return parser.parse_args()


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


def parse_ping_avg_rtt(ping_stdout: str):
    match = re.search(r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/", ping_stdout)
    return float(match.group(1)) if match else None


def main():
    args = parse_args()

    # Determine direction
    if args.reverse:
        src_host, dst_host = "h4", "h1"
        dst_ip = "10.0.0.1"
        csv_file = args.csv_out or "plot1_reverse_data.csv"
        plot_file = args.plot_out or "plot1_reverse_latency.png"
        direction_label = "H4 -> H1"
    else:
        src_host, dst_host = "h1", "h4"
        dst_ip = "10.0.0.4"
        csv_file = args.csv_out or "plot1_data.csv"
        plot_file = args.plot_out or "plot1_latency_vs_rate.png"
        direction_label = "H1 -> H4"

    src_pid = get_host_pid(src_host)
    dst_pid = get_host_pid(dst_host)

    if not src_pid or not dst_pid:
        print(f"Error: Mininet hosts {src_host} / {dst_host} not found. Is Mininet running?", file=sys.stderr)
        sys.exit(1)

    print(f"Running baseline benchmark for direction: {direction_label}")
    latencies = []

    try:
        subprocess.run(["sudo", "pkill", "-f", "iperf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

        run_in_host(dst_pid, ["iperf", "-s", "-u"], bg=True)
        time.sleep(1)

        for r in args.rates:
            print(f"Testing rate {r:>4.1f} Mbps: ", end="", flush=True)
            client_proc = run_in_host(src_pid, ["iperf", "-c", dst_ip, "-u", "-b", f"{r}M", "-t", "8"], bg=True)
            time.sleep(2)

            ping_res = run_in_host(src_pid, ["ping", "-c", "5", "-i", "0.5", dst_ip])
            client_proc.wait()

            avg_rtt = parse_ping_avg_rtt(ping_res.stdout)
            latencies.append(avg_rtt)
            print(f"RTT = {avg_rtt:.2f} ms" if avg_rtt else "DROP")
            time.sleep(1)

    finally:
        subprocess.run(["sudo", "pkill", "-f", "iperf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Save CSV
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rate_mbps", "avg_latency_ms"])
        for r, l in zip(args.rates, latencies):
            writer.writerow([r, l if l is not None else "DROP"])
    print(f"Data saved to {csv_file}")

    # Generate Plot
    valid = [(r, l) for r, l in zip(args.rates, latencies) if l is not None]
    if valid:
        x_vals, y_vals = zip(*valid)
        plt.figure(figsize=(8, 5))
        plt.plot(x_vals, y_vals, marker="o", linestyle="-", color="#0d47a1", linewidth=2, label="Measured Latency T")
        plt.axvline(x=10.0, color="#d32f2f", linestyle="--", label="Bottleneck Bandwidth B (10 Mbps)")
        plt.title(f"Plot 1: Latency $T$ vs $\\lambda$ ({direction_label})", fontsize=12)
        plt.xlabel("Injected Rate (Mbps)", fontsize=11)
        plt.ylabel("Round-Trip Latency $T$ (ms)", fontsize=11)
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(plot_file, dpi=300)
        print(f"Plot saved to {plot_file}")


if __name__ == "__main__":
    main()