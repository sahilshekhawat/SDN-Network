from pox.core import core
from pox.lib.addresses import IPAddr,EthAddr,parse_cidr
from pox.lib.revent import EventContinue,EventHalt
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpidToStr
import sys

log = core.getLogger()

#
virtual_ip_lb1 = IPAddr("10.0.0.10")
virtual_mac_lb1 = EthAddr("00:00:00:00:00:10")

virtual_ip_lb2 = IPAddr("10.0.0.20")
virtual_mac_lb2 = EthAddr("00:00:00:00:00:20")

server_lb1 = {}
server_lb1[0] = {'ip':IPAddr("10.0.0.5"), 'mac':EthAddr("00:00:00:00:00:05"), 'outport': 3}
server_lb1[1] = {'ip':IPAddr("10.0.0.6"), 'mac':EthAddr("00:00:00:00:00:06"), 'outport': 3}
total_servers_lb1 = len(server_lb1)


server_lb2 = {}
server_lb2[0] = {'ip':IPAddr("10.0.0.7"), 'mac':EthAddr("00:00:00:00:00:07"), 'outport': 3}
server_lb2[1] = {'ip':IPAddr("10.0.0.8"), 'mac':EthAddr("00:00:00:00:00:08"), 'outport': 3}
total_servers_lb2 = len(server_lb2)

#server_index = 0
server_index_lb1 = 0
server_index_lb2 = 0


def _handle_PacketIn (event):

    print "#########################################"
    print event.connection.dpid
    #global server_index
    global server_index_lb1
    global server_index_lb2
    packet = event.parsed

    # Only handle IPv4 flows
#    if (not event.parsed.find("ipv4")):
#        print "Was not Ipv4 packet, returning"
#        return EventContinue

    msg = of.ofp_flow_mod()
    msg.match = of.ofp_match.from_packet(packet)

    # Only handle traffic destined to virtual IP
    if (msg.match.nw_dst != virtual_ip_lb1 and msg.match.nw_dst != virtual_ip_lb2):
        print "Destination didn't matched, returning"
        return EventContinue

    # LB1
    global index
    global selected_server_ip
    global selected_server_mac
    global selected_server_outport

    if msg.match.nw_dst == virtual_ip_lb1:
        print "VIP_1 found"
        # Round robin selection of servers
        index = server_index_lb1 % total_servers_lb1
        print index
        selected_server_ip = server_lb1[index]['ip']
        selected_server_mac = server_lb1[index]['mac']
        selected_server_outport = server_lb1[index]['outport']
        server_index_lb1 += 1

    elif msg.match.nw_dst == virtual_ip_lb2:
        print "VIP_2 found"
        # Round robin selection of servers
        index = server_index_lb2 % total_servers_lb2
        print index
        selected_server_ip = server_lb2[index]['ip']
        selected_server_mac = server_lb2[index]['mac']
        selected_server_outport = server_lb2[index]['outport']
        server_index_lb2 += 1


    # Round robin selection of servers
    #index = server_index % total_servers
    #print index
    #selected_server_ip = server[index]['ip']
    #selected_server_mac = server[index]['mac']
    #selected_server_outport = server[index]['outport']
    #server_index += 1

    # Setup route to server
    msg.buffer_id = event.ofp.buffer_id
    msg.in_port = event.port

    msg.actions.append(of.ofp_action_dl_addr(of.OFPAT_SET_DL_DST, selected_server_mac))
    msg.actions.append(of.ofp_action_nw_addr(of.OFPAT_SET_NW_DST, selected_server_ip))
    msg.actions.append(of.ofp_action_output(port = selected_server_outport))
    event.connection.send(msg)

    # Setup reverse route from server
    reverse_msg = of.ofp_flow_mod()
    reverse_msg.buffer_id = None
    reverse_msg.in_port = selected_server_outport

    reverse_msg.match = of.ofp_match()
    reverse_msg.match.dl_src = selected_server_mac
    reverse_msg.match.nw_src = selected_server_ip
    reverse_msg.match.tp_src = msg.match.tp_dst

    reverse_msg.match.dl_dst = msg.match.dl_src
    reverse_msg.match.nw_dst = msg.match.nw_src
    reverse_msg.match.tp_dst = msg.match.tp_src


    if msg.match.nw_dst == virtual_ip_lb1:
        reverse_msg.actions.append(of.ofp_action_dl_addr(of.OFPAT_SET_DL_SRC, virtual_mac_lb1))
        reverse_msg.actions.append(of.ofp_action_nw_addr(of.OFPAT_SET_NW_SRC, virtual_ip_lb1))
    else:
        reverse_msg.actions.append(of.ofp_action_dl_addr(of.OFPAT_SET_DL_SRC, virtual_mac_lb2))
        reverse_msg.actions.append(of.ofp_action_nw_addr(of.OFPAT_SET_NW_SRC, virtual_ip_lb2))


#    reverse_msg.actions.append(of.ofp_action_dl_addr(of.OFPAT_SET_DL_SRC, virtual_mac))
#    reverse_msg.actions.append(of.ofp_action_nw_addr(of.OFPAT_SET_NW_SRC, virtual_ip))
    reverse_msg.actions.append(of.ofp_action_output(port = msg.in_port))
    event.connection.send(reverse_msg)

    return EventHalt

def launch ():
    # To intercept packets before the learning switch
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn, priority=2)

    log.info("Stateless LB running.")
