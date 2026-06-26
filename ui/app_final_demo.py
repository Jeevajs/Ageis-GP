"""
AEGIS Final UI launcher.

This final UI uses the Phase 9 + 10 interface because it includes the complete
end-to-end flow:
- OpenAI RCA
- Multi-agent planner
- GNN-style RCA output through the planner
- Neo4j KG explorer
- Human approval remediation
- Approval audit log
"""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "app_phase9_10.py"), run_name="__main__")
