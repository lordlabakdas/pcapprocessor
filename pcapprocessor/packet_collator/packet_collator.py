import pyshark

from pcapprocessor.packet_collator.stream_stats import StreamStats


class PacketCollator(StreamStats):
    def __init__(self, packet_stream: pyshark.FileCapture):
        self.packet_stream = packet_stream
        super().__init__()

    def connection_times(self):
        for packet in self.packet_stream:
            if not self.start_time:
                self.start_time = float(packet.sniff_time.timestamp())
            self.end_time = float(packet.sniff_time.timestamp())
        self.duration = self.end_time - self.start_time

    def collate(self):
        for packet in self.packet_stream:
            self.connection_times()
            self.total_bytes += int(packet.length)
        return self
