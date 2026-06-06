from unittest.mock import patch

from pcapprocessor.pbs.dce_runner import DceRunner


def test_run_with_scenario_delegates_to_bfs_runner(tmp_path):
    config_file = str(tmp_path / "config.cfg")
    with patch("pcapprocessor.pbs.dce_runner.BfsRunner") as mock_bfs:
        DceRunner(config_file, scenario="myScenario").run()
    mock_bfs.assert_called_once_with(config_file, "myScenario")
    mock_bfs.return_value.run.assert_called_once()


def test_run_without_scenario_delegates_to_pbs_writer(tmp_path):
    config_file = str(tmp_path / "config.cfg")
    with patch("pcapprocessor.pbs.dce_runner.PbsJobWriter") as mock_writer:
        DceRunner(config_file).run()
    mock_writer.assert_called_once_with(config_file, jobs_dir="initial-test")
    mock_writer.return_value.write.assert_called_once()


def test_custom_jobs_dir_passed_to_pbs_writer(tmp_path):
    config_file = str(tmp_path / "config.cfg")
    with patch("pcapprocessor.pbs.dce_runner.PbsJobWriter") as mock_writer:
        DceRunner(config_file, jobs_dir="custom-jobs").run()
    mock_writer.assert_called_once_with(config_file, jobs_dir="custom-jobs")


def test_init_stores_params():
    runner = DceRunner("cfg.cfg", scenario="s", jobs_dir="jobs")
    assert runner.config_file == "cfg.cfg"
    assert runner.scenario == "s"
    assert runner.jobs_dir == "jobs"
