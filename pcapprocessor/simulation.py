from configparser import ConfigParser


class QueueSizeCalculator:
    def __init__(self, scenario: str, x: str, config: ConfigParser):
        self.scenario = scenario
        self.x = x
        self.config = config

    def calculate(self) -> str:
        bdp_qsz = self.config.getfloat(self.scenario, "bdpQsz")
        xscale = self.config.get(self.scenario, self.scenario).split(",")

        if self.scenario == "bottleneckDelay":
            speed = self.config.get(self.scenario, "bottleneckSpeed")
            speed_numeric = self._parse_speed(speed)
            queue_size = int(
                bdp_qsz * speed_numeric * 2 * 0.001
                * (float(xscale[xscale.index(self.x)]) / 8)
            )

        elif self.scenario == "bottleneckSpeed":
            delay = int(self.config.get(self.scenario, "bottleneckDelay")[:-2])
            speed_unit = self.config.get(self.scenario, "speedUnit")
            x = self._apply_unit(int(self.x), speed_unit)
            queue_size = int(bdp_qsz * delay * 2 * 0.001 * (float(x) / 8))

        else:
            delay = int(self.config.get(self.scenario, "bottleneckDelay")[:-2])
            speed = self.config.get(self.scenario, "bottleneckSpeed")
            speed_numeric = self._parse_speed(speed)
            queue_size = int(
                bdp_qsz * speed_numeric * 2 * 0.001 * delay / 8
            )

        return str(queue_size)

    @staticmethod
    def _parse_speed(speed_str: str) -> int:
        unit = speed_str[-4:]
        numeric = int(speed_str[:-4])
        multipliers = {"K": 1_000, "M": 1_000_000, "G": 1_000_000_000}
        return multipliers.get(unit[0], 1) * numeric

    @staticmethod
    def _apply_unit(value: int, unit: str) -> int:
        multipliers = {"K": 1_000, "M": 1_000_000, "G": 1_000_000_000}
        return multipliers.get(unit[0], 1) * value


class WafCommandBuilder:
    def __init__(self, run_no: str, x: str, scenario: str, config: ConfigParser):
        self.run_no = run_no
        self.x = x
        self.scenario = scenario
        self.config = config

    def build(self) -> tuple:
        queue_size = QueueSizeCalculator(self.scenario, self.x, self.config).calculate()
        runs = self.config.getint(self.scenario, "runs")
        q_monitoring = 1 if runs == 1 else 0

        x = self.x
        if self.scenario in ("bottleneckDelay", "changingDelay"):
            x = x + "ms"
        elif self.scenario == "bottleneckSpeed":
            x = x + "Mbps"

        waf_cmd = self.config.get(
            section=self.scenario,
            option="cmd",
            vars=dict(
                queue_size=queue_size,
                x=x,
                runNo=self.run_no,
                qMonitoring=q_monitoring,
            ),
        )
        return waf_cmd, int(queue_size)
