from pathlib import Path

import pyshark

from pcapprocessor.packet_collator import PacketCollator


class PcapProcessor:
    def __init__(self, pcap_file_path: str, unit: str):
        self.pcap_file_path = Path(pcap_file_path)
        self.unit = unit

    def process(self) -> pyshark.FileCapture:
        packet_stream: pyshark.FileCapture = pyshark.FileCapture(
            self.pcap_file_path, keep_packets=False
        )
        packet_collator_obj = PacketCollator(packet_stream=packet_stream)
        packet_collator: PacketCollator = packet_collator_obj.collate()
