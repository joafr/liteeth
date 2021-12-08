#
# This file is part of LiteEth.
#
# Copyright (c) 2015-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

from liteeth.common import *
from liteeth.mac import LiteEthMAC, LiteEthMACSingleSource
from liteeth.core.arp import LiteEthARP
from liteeth.core.ip import LiteEthIP
from liteeth.core.udp import LiteEthUDP
from liteeth.core.icmp import LiteEthICMP
from litex.soc.interconnect.packet import PacketFIFO
from stream_additional.packet_fifo_reset import PacketFIFOReset

# IP Core ------------------------------------------------------------------------------------------

class LiteEthIPCore(Module, AutoCSR):
    def __init__(self, phy, mac_address, ip_address, clk_freq, with_icmp=True, dw=8):
        ip_address = convert_ip(ip_address)
        self.submodules.mac = LiteEthMAC(phy, dw, interface="crossbar", with_preamble_crc=True)
        self.submodules.arp = LiteEthARP(self.mac, mac_address, ip_address, clk_freq, dw=dw)
        self.submodules.ip  = LiteEthIP(self.mac, mac_address, ip_address, self.arp.table, dw=dw)
        if with_icmp:
            self.submodules.icmp = LiteEthICMP(self.ip, ip_address, dw=dw)

# UDP IP Core --------------------------------------------------------------------------------------

class LiteEthUDPIPCore(LiteEthIPCore):
    def __init__(self, phy, mac_address, ip_address, clk_freq, with_icmp=True, dw=8):
        ip_address = convert_ip(ip_address)
        LiteEthIPCore.__init__(self, phy, mac_address, ip_address, clk_freq, dw=dw,
                               with_icmp=with_icmp)
        self.submodules.udp = LiteEthUDP(self.ip, ip_address, dw=dw)


# IP Core modified ---------------------------------------------------------------------------------
class LiteEthIPCoreMod(Module, AutoCSR):
    def __init__(self, phy, mac_address, ip_address, dw=8,
                 with_packet_fifo=False, tx_only=False,
                 with_identification_counter=False):
            
        if with_packet_fifo:
            tx_fifo = PacketFIFO(eth_phy_description(phy.dw), 2048, buffered=False)
            tx_fifo = ClockDomainsRenamer("eth_tx")(tx_fifo)
            rx_fifo = PacketFIFOReset(eth_phy_description(phy.dw), 16384)
            rx_fifo = ClockDomainsRenamer("eth_rx")(rx_fifo)
            rx_tx_additional = (rx_fifo, tx_fifo)
        else:
            rx_tx_additional = (None, None)

        endianness = "little"
        ip_address = convert_ip(ip_address)
        if tx_only:
            self.submodules.mac = LiteEthMACSingleSource(phy, dw, with_preamble_crc=True,
                rx_tx_additional=rx_tx_additional, endianness=endianness)
        else:
            self.submodules.mac = LiteEthMAC(phy, dw, interface="crossbar", with_preamble_crc=True,
               rx_tx_additional=rx_tx_additional, endianness=endianness)
        self.submodules.ip  = LiteEthIP(self.mac, mac_address, ip_address, None, dw=dw, with_identification_counter=with_identification_counter)


# UDP IP Core modified ------------------------------------------------------------------------------
class LiteEthUDPIPCoreMod(LiteEthIPCoreMod):
    def __init__(self, phy, mac_address, ip_address, clk_freq, with_icmp=True, dw=8,
                 with_packet_fifo=False, tx_only=False,
                 with_identification_counter=False):
        ip_address = convert_ip(ip_address)
        LiteEthIPCoreMod.__init__(self, phy, mac_address, ip_address, dw=dw,
                                  with_packet_fifo=with_packet_fifo, tx_only=tx_only, 
                                  with_identification_counter=with_identification_counter)
        self.submodules.udp = LiteEthUDP(self.ip, ip_address, dw=dw)