import contextlib
import io
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from q_ai.analysis.assistant import ChemistryAssistant
from q_ai.cli import summarize, zmat
from q_ai.parser.qchem import QChemParser


def test_qchem_parser_extracts_core_properties():
    parser = QChemParser(PROJECT_ROOT / "examples" / "qchem" / "sample.out")

    result = parser.parse()

    assert result["total_energy"] == -152.81974151
    assert result["job_type"] == "SP"
    assert result["method"] == "HF"
    assert result["basis"] == "cc-pVDZ"


def test_chemistry_assistant_gives_actionable_summary():
    parser = QChemParser(PROJECT_ROOT / "examples" / "qchem" / "sample.out")
    assistant = ChemistryAssistant(parser.parse())

    summary = assistant.summarize()
    recommendations = assistant.recommendations()

    assert "HF" in summary
    assert "cc-pVDZ" in summary
    assert any("basis" in item.lower() or "method" in item.lower() for item in recommendations)


def test_cli_summary_accepts_explicit_subcommand():
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        summarize(["summarize", str(PROJECT_ROOT / "examples" / "qchem" / "sample.out")])

    rendered = output.getvalue()
    assert "HF" in rendered
    assert "cc-pVDZ" in rendered


def test_cli_zmat_writes_zmat_block(tmp_path):
    source = PROJECT_ROOT / "examples" / "qchem" / "CCO_opt_State1Add_EOMIP.out"
    temp_input = tmp_path / "CCO_opt_State1Add_EOMIP.out"
    temp_input.write_text(source.read_text())
    expected_output = tmp_path / "CCO_opt_State1Add_EOMIP.zmat"

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        zmat(["zmat", str(temp_input)])

    assert expected_output.exists()
    content = expected_output.read_text()
    assert content.startswith("ABC\n")
    assert "C\nH  1 R1\nH  1 R2 2 A1" in content
    assert "O  1 R3 2 A2 3 T1" in content
    assert "R1 = 1.107654" in content
    assert "A1 = 102.411426" in content
    assert "T1 = -105.048361" in content
    assert "CHARGE = -1, MULT = 2" in content
    assert "Wrote" in output.getvalue()
    assert "CCO_opt_State1Add_EOMIP.zmat" in output.getvalue()
