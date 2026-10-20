


#!/usr/bin/env python3
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info


class ProjectTopo(Topo):
    def build(self):
        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', ip='10.0.0.4/24', mac='00:00:00:00:00:04')

        switches = {}
        for i in range(1, 7):
            switches[f's{i}'] = self.addSwitch(f's{i}', protocols='OpenFlow13')

        link_opts = dict(bw=10, delay='5ms', max_queue_size=100)

        # Host links
        self.addLink(h1, switches['s1'], port1=1, port2=1, **link_opts)
        self.addLink(h2, switches['s2'], port1=1, port2=1, **link_opts)
        self.addLink(h3, switches['s3'], port1=1, port2=1, **link_opts)
        self.addLink(h4, switches['s4'], port1=1, port2=1, **link_opts)

        # Path 1: s1 -> s2 -> s3 -> s4
        self.addLink(switches['s1'], switches['s2'], port1=2, port2=2, **link_opts)
        self.addLink(switches['s2'], switches['s3'], port1=3, port2=2, **link_opts)
        self.addLink(switches['s3'], switches['s4'], port1=3, port2=2, **link_opts)

        # Path 2: s1 -> s5 -> s6 -> s4
        self.addLink(switches['s1'], switches['s5'], port1=3, port2=1, **link_opts)
        self.addLink(switches['s5'], switches['s6'], port1=2, port2=1, **link_opts)
        self.addLink(switches['s6'], switches['s4'], port1=2, port2=3, **link_opts)


def run():
    topo = ProjectTopo()
    net = Mininet(topo=topo, link=TCLink, switch=OVSSwitch, controller=None)
    net.start()
    info("Topology running. Starting CLI...\n")
    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()