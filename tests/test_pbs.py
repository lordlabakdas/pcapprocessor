import os
from pcapprocessor.pbs.job_writer import PbsJobWriter


def test_pbs_job_writer_creates_jobs_dir(tmp_path):
    jobs_dir = str(tmp_path / "jobs")
    writer = PbsJobWriter("test.cfg", jobs_dir=jobs_dir)
    writer.write()
    assert os.path.isdir(jobs_dir)


def test_pbs_job_writer_creates_pbs_files(tmp_path):
    jobs_dir = str(tmp_path / "jobs")
    writer = PbsJobWriter("test.cfg", jobs_dir=jobs_dir)
    writer.write()
    pbs_files = [f for f in os.listdir(jobs_dir) if f.endswith(".pbs")]
    assert len(pbs_files) > 0


def test_pbs_job_writer_creates_driver_script(tmp_path):
    jobs_dir = str(tmp_path / "jobs")
    writer = PbsJobWriter("test.cfg", jobs_dir=jobs_dir)
    writer.write()
    assert os.path.exists(os.path.join(jobs_dir, "driver.sh"))


def test_pbs_job_writer_write_single_creates_pbs(tmp_path):
    jobs_dir = str(tmp_path / "jobs")
    writer = PbsJobWriter("error_test.cfg", jobs_dir=jobs_dir)
    writer.write_single()
    pbs_files = [f for f in os.listdir(jobs_dir) if f.endswith(".pbs")]
    assert len(pbs_files) == 1
