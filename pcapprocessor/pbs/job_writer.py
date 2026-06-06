import os


class PbsJobWriter:
    _NODE_SPECS_SIMPLE = "#PBS -l nodes=1:ppn=2,mem=1000M"
    _NODE_SPECS_CFG = "#PBS -l nodes=1:ppn=2,mem=2000M,walltime=120:0:0"

    def __init__(
        self,
        config_file: str,
        jobs_dir: str,
        email: str = "",
        work_dir: str = "",
    ):
        self.config_file = config_file
        self.jobs_dir = jobs_dir
        self.email = email
        self.work_dir = work_dir
        self._cfg_name = config_file[:-4]

    def write(self) -> None:
        """Generate PBS job files for TCP variants × scenarios (was pbsWriter)."""
        tcp_variants = ["bic"]
        scenarios = ["error"]
        os.makedirs(self.jobs_dir, exist_ok=True)
        driver_path = os.path.join(self.jobs_dir, "driver.sh")

        with open(driver_path, "w") as driver_file:
            for tcp in tcp_variants:
                for scen in scenarios:
                    pbs_name = self._write_job(tcp, scen)
                    driver_file.write("qsub " + pbs_name + "\n")

    def write_single(self) -> None:
        """Generate a single PBS job for this config file (was cfgPbsWriter)."""
        scenario = self.config_file.split("_", 1)[0]
        cfg_id = self._cfg_name
        os.makedirs(self.jobs_dir, exist_ok=True)

        pbs_filename = os.path.join(self.jobs_dir, cfg_id + ".pbs")
        run_cmd = (
            "python " + self.work_dir + "dceRunner.py "
            + self.config_file + " " + scenario
        )
        run_dir = "/tmp/tmp_" + cfg_id

        with open(pbs_filename, "w") as pbs_file:
            pbs_file.write(self._NODE_SPECS_CFG + "\n")
            pbs_file.write("#PBS -j oe\n")
            pbs_file.write("#PBS -S /bin/sh\n")
            pbs_file.write("#PBS -M " + self.email + "\n")
            pbs_file.write("#PBS -m a\n")
            pbs_file.write("#PBS -N " + cfg_id + "\n\n")
            pbs_file.write("cd $PBS_O_WORKDIR\n")
            pbs_file.write("cd " + self.work_dir + "\n")
            pbs_file.write("mkdir " + run_dir + "\n")
            pbs_file.write("cp " + self.config_file + " " + run_dir + "\n")
            pbs_file.write("cd " + run_dir + "\n")
            pbs_file.write(run_cmd + "\n")
            pbs_file.write("mv *.csv *.mon " + self.work_dir + "\n")
            pbs_file.write("cd " + run_dir + "\n")
            pbs_file.write("rm -rf " + run_dir + "\n")

    def _write_job(self, tcp: str, scen: str) -> str:
        unique_id = self._cfg_name + "_" + tcp + "_" + scen
        run_dir = "tmp_" + unique_id
        run_cmd = (
            "python ../dceRunner.py " + self.config_file
            + " " + scen + " " + tcp
        )
        pbs_fi_name = unique_id + ".pbs"
        pbs_path = os.path.join(self.jobs_dir, pbs_fi_name)

        with open(pbs_path, "w") as pbs_file:
            pbs_file.write(self._NODE_SPECS_SIMPLE + "\n")
            pbs_file.write("#PBS -j oe\n")
            pbs_file.write("#PBS -S /bin/sh\n")
            pbs_file.write("#PBS -M " + self.email + "\n")
            pbs_file.write("#PBS -m abe\n")
            pbs_file.write("#PBS -N " + unique_id + "\n\n")
            pbs_file.write("cd $PBS_O_WORKDIR\n")
            pbs_file.write("cd " + self.work_dir + "\n")
            pbs_file.write("mkdir " + run_dir + "\n")
            pbs_file.write("cp " + self.config_file + " " + run_dir + "\n")
            pbs_file.write("cd " + run_dir + "\n")
            pbs_file.write(run_cmd + "\n")
            pbs_file.write("mv *.csv ../\n")
            pbs_file.write("cd ..\n")
            pbs_file.write("rm -rf " + run_dir + "\n")

        return pbs_fi_name
