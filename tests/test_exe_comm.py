import subprocess
from unittest.mock import MagicMock, patch

from pcapprocessor.exe_comm import exe_comm


def test_capture_true_returns_stdout():
    mock_result = MagicMock()
    mock_result.stdout = b"hello world"
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = exe_comm(["echo", "hello"])
    assert result == "hello world"
    mock_run.assert_called_once_with(
        ["echo", "hello"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def test_capture_false_returns_empty_string():
    with patch("subprocess.run") as mock_run:
        result = exe_comm(["echo", "hello"], capture=False)
    assert result == ""
    mock_run.assert_called_once_with(["echo", "hello"], check=True)


def test_non_ascii_output_decoded_with_replace():
    mock_result = MagicMock()
    mock_result.stdout = "héllo".encode("utf-8")
    with patch("subprocess.run", return_value=mock_result):
        result = exe_comm(["cmd"])
    assert result == "héllo"
