from pcapprocessor.metrics_calculator.metrics import Metrics


class MetricsCalculator(Metrics):
    def __init__(self, total_bytes: int, start_time: int, end_time: int, duration: int):
        self.total_bytes = total_bytes
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
    
    def calculate_throughput(self) -> Metrics:
        self.throughput = float(self.total_bytes / self.duration)
        return self
    
    def __dict__(self):
        self.calculate_throughput()
        self.__dict__
