from __future__ import annotations

from typing import Any, Dict


class ChemistryAssistant:
    """Turn parsed quantum chemistry output into a compact, human-readable summary."""

    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def summarize(self) -> str:
        method = self.data.get("method", "unknown")
        basis = self.data.get("basis", "unknown")
        energy = self.data.get("total_energy")
        job_type = self.data.get("job_type", "unknown")

        energy_text = f"{energy:.8f}" if isinstance(energy, (int, float)) else "not available"
        return (
            f"This {job_type} calculation used {method} with the {basis} basis set "
            f"and reported a total energy of {energy_text}."
        )

    def recommendations(self) -> list[str]:
        recommendations = []
        method = self.data.get("method", "")
        basis = self.data.get("basis", "")

        if method == "HF":
            recommendations.append("Consider a post-HF method such as MP2 or CCSD(T) for correlation effects.")
        if basis in {"cc-pVDZ", "sto-3g"}:
            recommendations.append("Try a larger basis set such as cc-pVTZ to improve accuracy.")
        if not recommendations:
            recommendations.append("Review the chosen method and basis set for stronger chemical accuracy.")
        return recommendations
