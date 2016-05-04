
TOPOLOGY
========
```
h1-----|                    |----h5
       |--s1--|      |--s3--|
h2-----|      |      |      |----h6
              |--s5--|
h1-----|      |      |      |----h7
       |--s1--|      |--s4--|
h2-----|                    |----h8
```
Hosts
-----
HTTP only: h2, h4
HTTP/HTTPS: h1, h3

Servers
-------
Load balancer 1:
  Hosts: h5, h6
  Virtual IP: 10.0.0.10

Load balancer 2:
  Hosts: h7, h8
  Virtual IP: 10.0.0.20



Running
=======

1. Run Mininet VM [Mininet VM](http://mininet.org/download/)
2. Clone this repo: ``git clone git@github.com:sahilshekhawat/SDN-Network.git``
3. Run Mininet using topology ``sudo ./topology``.
4. Copy firewall.py to pox/pox/misc/, load_balancer.py and l2_learning.py to pox/pox/forwarding.
5. Run controller: ``pox.py forwarding.load_balancer forwarding.l2_learning misc.firewall``
6. Add arp entry in hosts e.g. on h1 ``arp -s 10.0.0.10 00:00:00:00:10``
