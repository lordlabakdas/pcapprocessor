from pcapprocessor.pbs.job_writer import PbsJobWriter
from pcapprocessor.runner import BfsRunner


class DceRunner:
    def __init__(self, config_file: str, scenario: str = None, jobs_dir: str = "initial-test"):
        self.config_file = config_file
        self.scenario = scenario
        self.jobs_dir = jobs_dir

    def run(self) -> None:
        if self.scenario:
            BfsRunner(self.config_file, self.scenario).run()
        else:
            PbsJobWriter(self.config_file, jobs_dir=self.jobs_dir).write()
