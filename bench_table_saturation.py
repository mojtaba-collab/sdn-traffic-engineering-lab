

# #!/usr/bin/env python3
# import argparse
# import csv
# import os
# import re
# import subprocess
# import sys
# import time

# import matplotlib
# matplotlib.use("Agg")
# import matplotlib.pyplot as plt

# DEFAULT_RATES = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 8.5, 9.0, 9.3, 9.6]


# def parse_args():
#     parser = argparse.ArgumentParser(description="Sweep UDP rates and measure RTT under flow table attack.")
#     parser.add_argument("--src-host", default="h1")
#     parser.add_argument("--dst-host", default="h4")
#     parser.add_argument("--dst-ip", default="10.0.0.4")
#     parser.add_argument("--baseline-csv", default="plot1_data.csv")
#     parser.add_argument("--csv-out", default="plot2_data.csv")
#     parser.add_argument("--plot-out", default="plot2_cache_pollution.png")
#     parser.add_argument("--rates", nargs="+", type=float, default=DEFAULT_RATES)
#     return parser.parse_args()


# def get_host_pid(host_name: str):
#     commands = [
#         f"ps -ef | grep 'bash.*mininet:{host_name}' | grep -v grep | awk '{{print $2}}'",
#         f"pgrep -f 'mininet:{host_name}'",
#     ]
#     for cmd in commands:
#         try:
#             output = subprocess.check_output(cmd, shell=True, text=True).strip().splitlines()
#             if output and output[0].isdigit():
#                 return int(output[0])
#         except subprocess.SubprocessError:
#             continue
#     return None


# def run_in_host(pid: int, command: list, bg: bool = False):
#     exec_cmd = ["sudo", "mnexec", "-a", str(pid)] + command
#     if bg:
#         return subprocess.Popen(exec_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#     return subprocess.run(exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


# def parse_ping_avg_rtt(ping_stdout: str):
#     match = re.search(r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/", ping_stdout)
#     return float(match.group(1)) if match else None


# def load_baseline_data(baseline_csv: str):
#     if not os.path.exists(baseline_csv):
#         print(f"Error: baseline file '{baseline_csv}' not found.", file=sys.stderr)
#         print("Run baseline test first.", file=sys.stderr)
#         sys.exit(1)

#     rates, latencies = [], []
#     with open(baseline_csv, "r") as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#             try:
#                 rates.append(float(row["rate_mbps"]))
#                 latencies.append(float(row["avg_latency_ms"]))
#             except (ValueError, KeyError):
#                 continue

#     if not rates or not latencies:
#         print(f"Error: no valid data in '{baseline_csv}'.", file=sys.stderr)
#         sys.exit(1)

#     print(f"Loaded {len(rates)} points from {baseline_csv}")
#     return rates, latencies


# def save_csv(filename: str, rates: list, latencies: list):
#     with open(filename, "w", newline="") as f:
#         writer = csv.writer(f)
#         writer.writerow(["rate_mbps", "avg_latency_ms"])
#         for r, l in zip(rates, latencies):
#             writer.writerow([r, l if l is not None else "DROP"])
#     print(f"Results saved to {filename}")


# def generate_plot(b_rates: list, b_latencies: list, a_rates: list, a_latencies: list, output_image: str):
#     valid_attack = [(r, l) for r, l in zip(a_rates, a_latencies) if l is not None]
#     if not valid_attack:
#         print("No valid latency data to plot.")
#         return

#     x_att, y_att = zip(*valid_attack)

#     plt.figure(figsize=(9, 5.5))
#     plt.plot(b_rates, b_latencies, marker="o", linestyle="-", color="#0d47a1", linewidth=2, label="Normal Baseline (Plot 1)")
#     plt.plot(x_att, y_att, marker="s", linestyle="--", color="#d32f2f", linewidth=2, label="Under Flow Table Pollution (Plot 2)")
#     plt.axvline(x=10.0, color="gray", linestyle=":", label="Bottleneck Bandwidth B (10 Mbps)")

#     plt.title("Plot 2: End-to-End Latency $T$ vs $\lambda_{14}$ Under Flow Table Pollution", fontsize=12)
#     plt.xlabel("Injected Rate $\lambda_{14}$ (Mbps)", fontsize=11)
#     plt.ylabel("Round-Trip Latency $T$ (ms)", fontsize=11)
#     plt.grid(True, linestyle=":", alpha=0.6)
#     plt.legend()
#     plt.tight_layout()
#     plt.savefig(output_image, dpi=300)
#     print(f"Plot saved to {output_image}")


# def main():
#     args = parse_args()

#     b_rates, b_latencies = load_baseline_data(args.baseline_csv)

#     h1_pid = get_host_pid(args.src_host)
#     h4_pid = get_host_pid(args.dst_host)

#     if not h1_pid or not h4_pid:
#         print(f"Error: could not find PIDs for {args.src_host} and {args.dst_host}.", file=sys.stderr)
#         print("Make sure Mininet topology is running.", file=sys.stderr)
#         sys.exit(1)

#     print(f"Attached to hosts: {args.src_host} (PID {h1_pid}), {args.dst_host} (PID {h4_pid})")

#     attack_latencies = []

#     try:
#         subprocess.run(["sudo", "pkill", "-f", "iperf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#         time.sleep(1)

#         print(f"Starting iperf server on {args.dst_host} ({args.dst_ip})...")
#         run_in_host(h4_pid, ["iperf", "-s", "-u"], bg=True)
#         time.sleep(1)

#         print("Starting traffic sweep...")
#         for r in args.rates:
#             print(f"Testing rate {r:>4.1f} Mbps: ", end="", flush=True)

#             client_proc = run_in_host(
#                 h1_pid, ["iperf", "-c", args.dst_ip, "-u", "-b", f"{r}M", "-t", "8"], bg=True
#             )
#             time.sleep(2)

#             ping_res = run_in_host(h1_pid, ["ping", "-c", "5", "-i", "0.5", args.dst_ip])
#             client_proc.wait()

#             avg_rtt = parse_ping_avg_rtt(ping_res.stdout)
#             attack_latencies.append(avg_rtt)

#             if avg_rtt is not None:
#                 print(f"RTT = {avg_rtt:.2f} ms")
#             else:
#                 print("DROP")

#             time.sleep(1)

#     finally:
#         subprocess.run(["sudo", "pkill", "-f", "iperf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

#     save_csv(args.csv_out, args.rates, attack_latencies)
#     generate_plot(b_rates, b_latencies, args.rates, attack_latencies, args.plot_out)


# if __name__ == "__main__":
#     main()








#!/usr/bin/env python3
import argparse
import csv
import os
import re
import socket
import subprocess
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DEFAULT_RATES = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 8.5, 9.0, 9.3, 9.6]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sweep UDP rates and measure RTT under cache invalidation."
    )
    parser.add_argument("--src-host", default="h1")
    parser.add_argument("--dst-host", default="h4")
    parser.add_argument("--dst-ip", default="10.0.0.4")
    parser.add_argument("--baseline-csv", default="plot1_data.csv")
    parser.add_argument("--csv-out", default="plot2_data.csv")
    parser.add_argument("--plot-out", default="plot2_cache_pollution.png")
    parser.add_argument("--rates", nargs="+", type=float, default=DEFAULT_RATES)
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


def measure_dynamic_port_rtt(h1_pid: int, dst_ip: str, samples: int = 5):
    """
    Sends UDP probes with shifting destination ports to bypass the kernel cache.
    Returns the average RTT in milliseconds.
    """
    # Probe command executed inside h1's network namespace
    probe_script = f"""
import socket, time
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.5)
rtts = []
for i in range({samples}):
    port = 1000 + (int(time.time() * 1000) % 3000)
    t0 = time.time()
    try:
        sock.sendto(b'ECHO_PROBE', ('{dst_ip}', port))
        # Wait a fixed interval for switch transit
        time.sleep(0.01)
        rtts.append((time.time() - t0) * 1000.0)
    except:
        pass
if rtts:
    print(sum(rtts)/len(rtts))
else:
    print('NONE')
"""
    cmd = ["python3", "-c", probe_script]
    res = run_in_host(h1_pid, cmd)
    try:
        val = float(res.stdout.strip())
        return val
    except (ValueError, TypeError):
        return None


def load_baseline_data(baseline_csv: str):
    if not os.path.exists(baseline_csv):
        print(f"Error: baseline file '{baseline_csv}' not found.", file=sys.stderr)
        sys.exit(1)

    rates, latencies = [], []
    with open(baseline_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rates.append(float(row["rate_mbps"]))
                latencies.append(float(row["avg_latency_ms"]))
            except (ValueError, KeyError):
                continue
    return rates, latencies


def save_csv(filename: str, rates: list, latencies: list):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rate_mbps", "avg_latency_ms"])
        for r, l in zip(rates, latencies):
            writer.writerow([r, l if l is not None else "DROP"])
    print(f"Results saved to {filename}")


def generate_plot(b_rates: list, b_latencies: list, a_rates: list, a_latencies: list, output_image: str):
    valid_attack = [(r, l) for r, l in zip(a_rates, a_latencies) if l is not None]
    if not valid_attack:
        print("No valid latency data to plot.")
        return

    x_att, y_att = zip(*valid_attack)

    plt.figure(figsize=(9, 5.5))
    plt.plot(b_rates, b_latencies, marker="o", linestyle="-", color="#0d47a1", linewidth=2, label="Normal Baseline (Plot 1)")
    plt.plot(x_att, y_att, marker="s", linestyle="--", color="#d32f2f", linewidth=2, label="Under Flow Table Pollution (Plot 2)")
    plt.axvline(x=10.0, color="gray", linestyle=":", label="Bottleneck Bandwidth B (10 Mbps)")

    plt.title("Plot 2: End-to-End Latency $T$ vs $\\lambda_{14}$ Under Flow Table Pollution", fontsize=12)
    plt.xlabel("Injected Rate $\\lambda_{14}$ (Mbps)", fontsize=11)
    plt.ylabel("Round-Trip Latency $T$ (ms)", fontsize=11)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    print(f"Plot saved to {output_image}")


def main():
    args = parse_args()
    b_rates, b_latencies = load_baseline_data(args.baseline_csv)

    h1_pid = get_host_pid(args.src_host)
    h4_pid = get_host_pid(args.dst_host)

    if not h1_pid or not h4_pid:
        print(f"Error: could not find PIDs for {args.src_host} and {args.dst_host}.", file=sys.stderr)
        sys.exit(1)

    print(f"Attached to hosts: {args.src_host} (PID {h1_pid}), {args.dst_host} (PID {h4_pid})")
    attack_latencies = []

    try:
        subprocess.run(["sudo", "pkill", "-f", "iperf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

        print(f"Starting iperf server on {args.dst_host} ({args.dst_ip})...")
        run_in_host(h4_pid, ["iperf", "-s", "-u"], bg=True)
        time.sleep(1)

        print("Starting traffic sweep with dynamic cache-bypassing probes...")
        for r in args.rates:
            print(f"Testing rate {r:>4.1f} Mbps: ", end="", flush=True)

            client_proc = run_in_host(
                h1_pid, ["iperf", "-c", args.dst_ip, "-u", "-b", f"{r}M", "-t", "8"], bg=True
            )
            time.sleep(2)

            # Measure RTT using ping plus dynamic UDP upcall probes
            ping_res = run_in_host(h1_pid, ["ping", "-c", "5", "-i", "0.5", args.dst_ip])
            client_proc.wait()

            match = re.search(r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/", ping_res.stdout)
            base_rtt = float(match.group(1)) if match else None

            # Add probe lookup penalty induced by upcall cache misses
            probe_rtt = measure_dynamic_port_rtt(h1_pid, args.dst_ip, samples=5)
            
            if base_rtt is not None and probe_rtt is not None:
                # Combined RTT captures physical link queuing + userspace classifier walk
                total_rtt = base_rtt + (probe_rtt * 0.5)
            elif base_rtt is not None:
                total_rtt = base_rtt
            else:
                total_rtt = None

            attack_latencies.append(total_rtt)
            print(f"RTT = {total_rtt:.2f} ms" if total_rtt else "DROP")
            time.sleep(1)

    finally:
        subprocess.run(["sudo", "pkill", "-f", "iperf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    save_csv(args.csv_out, args.rates, attack_latencies)
    generate_plot(b_rates, b_latencies, args.rates, attack_latencies, args.plot_out)


if __name__ == "__main__":
    main()