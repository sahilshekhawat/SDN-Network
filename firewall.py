from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.addresses import EthAddr
from collections import namedtuple
import os

import csv

log = core.getLogger()
policyFile = "%s/pox/pox/misc/firewall-policies.csv" % os.environ[ 'HOME' ]
  
class Firewall (EventMixin):

    def __init__ (self):
        self.listenTo(core.openflow)
        log.debug("Enabling Firewall Module")
        self.deny = []
        with open(policyFile, 'rb') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.deny.append(EthAddr(row['src']))

    def _handle_ConnectionUp (self, event):
        for src in self.deny:
            match = of.ofp_match()
            match.tp_dst = 443
            match.nw_proto = 6
            match.dl_type = 0x800
            match.dl_src = src
            msg = of.ofp_flow_mod()
            msg.match = match
            event.connection.send(msg)
        log.debug("Firewall rules installed on %s", dpidToStr(event.dpid))

def launch ():

    core.registerNew(Firewall)
