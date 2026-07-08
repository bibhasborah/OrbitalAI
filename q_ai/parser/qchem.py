"""
Q-Chem output parser for Q-AI.

Version: 0.1
Author: Bibhas Borah
"""

from pathlib import Path
import re


class QChemParser:
    """Parser for Q-Chem output files."""

    def __init__(self, filename):
        self.filename = Path(filename)

        with open(self.filename, "r") as f:
            self.text = f.read()

    def total_energy(self):
        """Return the last total energy found in the output."""

        pattern = r"Total energy(?: in the final basis set)?\s*=\s*(-?\d+\.\d+)"
        energies = re.findall(pattern, self.text)

        if len(energies) == 0:
            return None

        return float(energies[-1])

    def _extract_rem_value(self, key: str):
        pattern = rf"^\s*{re.escape(key)}\s*=\s*(.+)$"
        for line in self.text.splitlines():
            match = re.match(pattern, line, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip().strip("'").strip('"')
        return None

    def parse(self):
        """Return parsed Q-Chem values."""

        return {
            "total_energy": self.total_energy(),
            "job_type": self._extract_rem_value("JOB_TYPE"),
            "method": self._extract_rem_value("METHOD"),
            "basis": self._extract_rem_value("BASIS"),
        }
