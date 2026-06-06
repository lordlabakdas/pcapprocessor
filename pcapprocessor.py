from pcapprocessor.processor import PcapProcessor

__all__ = ["PcapProcessor"]


if __name__ == "__main__":
    import sys
    from configparser import ConfigParser

    if len(sys.argv) < 7:
        print(
            "Usage: python pcapprocessor.py <pcap_file> <unit> <config_file>"
            " <scenario> <ascii_trace_file> <buf_size>"
        )
        sys.exit(1)

    cfg = ConfigParser()
    cfg.read(sys.argv[3])

    proc = PcapProcessor(
        pcap_file_path=sys.argv[1],
        unit=sys.argv[2],
        config=cfg,
        scenario=sys.argv[4],
        ascii_trace_file=sys.argv[5],
        buf_size=int(sys.argv[6]),
    )
    result = proc.process()
    print(result)
