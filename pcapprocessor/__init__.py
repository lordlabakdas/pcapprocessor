import importlib.util
from pathlib import Path

# Load PcapProcessor from the root pcapprocessor.py module
_root_module_path = Path(__file__).parent.parent / "pcapprocessor.py"
spec = importlib.util.spec_from_file_location("_pcapprocessor_root", _root_module_path)
_root_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_root_module)

PcapProcessor = _root_module.PcapProcessor

__all__ = ["PcapProcessor"]
