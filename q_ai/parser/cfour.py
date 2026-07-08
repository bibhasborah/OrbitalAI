from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


class CfourZmatWriter:
    """Write a CFOUR Z-matrix input file from a Q-Chem output file."""

    def __init__(self, qchem_output_file: Path):
        self.qchem_output_file = Path(qchem_output_file)

    @staticmethod
    def _parse_original_charge_multiplicity(text: str) -> tuple[int, int]:
        match = re.search(r"^\$molecule\s*$", text, flags=re.MULTILINE)
        if not match:
            return 0, 1

        tail = text[match.end():]
        for line in tail.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("$"):
                continue
            parts = stripped.split()
            if len(parts) >= 2 and re.fullmatch(r"-?\d+", parts[0]) and re.fullmatch(r"\d+", parts[1]):
                return int(parts[0]), int(parts[1])
            break

        return 0, 1

    @staticmethod
    def _detect_state_type(text: str) -> str:
        if re.search(r"\bIP_STATES\b", text, flags=re.IGNORECASE) or re.search(r"EOMIP", text, flags=re.IGNORECASE):
            return "IP"
        if re.search(r"\bEA_STATES\b", text, flags=re.IGNORECASE) or re.search(r"EOMEA", text, flags=re.IGNORECASE):
            return "EA"
        # Accept both spaced and underscore forms used in various outputs
        if re.search(r"\bDIP\s*SINGLETS\b", text, flags=re.IGNORECASE) or re.search(r"\bDIP_SINGLETS\b", text, flags=re.IGNORECASE):
            return "DIP_SINGLETS"
        if re.search(r"\bDIP\s*TRIPLETS\b", text, flags=re.IGNORECASE) or re.search(r"\bDIP_TRIPLETS\b", text, flags=re.IGNORECASE):
            return "DIP_TRIPLETS"
        return "NONE"

    @staticmethod
    def _infer_charge_and_mult(state_type: str, original_charge: int, original_mult: int) -> tuple[int, int]:
        if state_type == "IP":
            return original_charge + 1, 2
        if state_type == "EA":
            return original_charge - 1, 2
        if state_type == "DIP_SINGLETS":
            return 0, 1
        if state_type == "DIP_TRIPLETS":
            return 0, 3
        return original_charge, original_mult

    @staticmethod
    def _make_cfour_header(charge: int, multiplicity: int) -> str:
        return (
            "*CFOUR(CALC=CCSD(T), BASIS=AUG-PVTZ\n"
            "REF = UHF, CC_PROG=VCC\n"
            "GEO_CONV=7, SCF_CONV=10, CC_CONV=10, LINEQ_CONV=10\n"
            "SCF_MAXCYC = 200, CC_MAXCYC = 200\n"
            f"CHARGE = {charge}, MULT = {multiplicity}\n"
            "FROZEN_CORE=ON, MEM_UNIT=GB, MEM=64)\n"
        )

    def _make_zmat_text(self, text: str) -> str:
        match = re.search(r"Z-matrix Print:\s*(.*?)^\$end\s*$", text, flags=re.DOTALL | re.MULTILINE)
        if not match:
            raise ValueError("No Z-matrix block found in Q-Chem output.")

        zmat_block = match.group(1).strip().splitlines()
        if not zmat_block or not zmat_block[0].strip().startswith("$molecule"):
            raise ValueError("Z-matrix block does not start with a $molecule section.")

        raw_lines = []
        first_line = True
        for line in zmat_block[1:]:
            stripped = line.strip()
            if stripped == "$end":
                break
            if not stripped:
                continue
            parts = stripped.split()
            if first_line and len(parts) == 2 and all(re.fullmatch(r"-?\d+", token) for token in parts):
                # Q-Chem Z-matrix prints a charge/multiplicity line immediately after $molecule.
                first_line = False
                continue
            first_line = False
            raw_lines.append(parts)

        if not raw_lines:
            raise ValueError("Empty Z-matrix block.")

        variable_lines = []
        r_count = 1
        a_count = 1
        t_count = 1
        assignments = []

        for parts in raw_lines:
            symbol = parts[0]
            if len(parts) == 1:
                variable_lines.append(symbol)
                continue

            atom1 = parts[1]
            distance = parts[2]
            r_name = f"R{r_count}"
            assignments.append(f"{r_name} = {distance}")
            r_count += 1

            if len(parts) == 3:
                variable_lines.append(f"{symbol}  {atom1} {r_name}")
                continue

            atom2 = parts[3]
            angle = parts[4]
            a_name = f"A{a_count}"
            assignments.append(f"{a_name} = {angle}")
            a_count += 1

            if len(parts) == 5:
                variable_lines.append(f"{symbol}  {atom1} {r_name} {atom2} {a_name}")
                continue

            atom3 = parts[5]
            dihedral = parts[6]
            t_name = f"T{t_count}"
            assignments.append(f"{t_name} = {dihedral}")
            t_count += 1

            variable_lines.append(f"{symbol}  {atom1} {r_name} {atom2} {a_name} {atom3} {t_name}")

        output_lines = ["ABC"]
        output_lines.extend(variable_lines)
        output_lines.append("")
        output_lines.extend(assignments)
        return "\n".join(output_lines) + "\n"

    def _format_output(self, text: str) -> str:
        zmat_text = self._make_zmat_text(text)
        original_charge, original_mult = self._parse_original_charge_multiplicity(text)
        state_type = self._detect_state_type(text)
        charge, multiplicity = self._infer_charge_and_mult(state_type, original_charge, original_mult)

        output_lines = [zmat_text.rstrip(), ""]
        output_lines.append(self._make_cfour_header(charge, multiplicity).rstrip())
        return "\n".join(output_lines) + "\n"

    @property
    def output_filename(self) -> Path:
        return self.qchem_output_file.with_suffix(".zmat")

    def write(self, output_file: Optional[Path] = None) -> Path:
        output_file = Path(output_file) if output_file else self.output_filename
        text = self.qchem_output_file.read_text()
        zmat = self._format_output(text)

        output_file.write_text(zmat)
        return output_file
