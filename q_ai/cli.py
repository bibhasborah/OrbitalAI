from __future__ import annotations

import argparse
from pathlib import Path
import sys

from q_ai.analysis.assistant import ChemistryAssistant
from q_ai.parser.cfour import CfourZmatWriter
from q_ai.parser.qchem import QChemParser


COMMAND_ALIASES = {
    "summarize": "summarize",
    "summary": "summarize",
    "totalenergy": "totalenergy",
    "zmat": "zmat",
    "fZMT": "zmat",
}


def _resolve_args(argv=None, default_command="summarize"):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in COMMAND_ALIASES:
        command = COMMAND_ALIASES[argv.pop(0)]
    else:
        command = default_command
    return command, argv


def totalenergy(argv=None):
    command, args = _resolve_args(argv, default_command="totalenergy")
    if command != "totalenergy":
        raise SystemExit("totalenergy expects a file path")

    parser = argparse.ArgumentParser(description="Print the total energy from a Q-Chem output file.")
    parser.add_argument("output_file", type=Path, help="Q-Chem output file to parse")
    parsed_args = parser.parse_args(args)

    energy = QChemParser(parsed_args.output_file).total_energy()
    if energy is None:
        parser.error(f"no total energy found in {parsed_args.output_file}")

    print(energy)


def summarize(argv=None):
    command, args = _resolve_args(argv, default_command="summarize")
    if command not in {"summarize", "summary"}:
        raise SystemExit("summarize expects a file path")

    parser = argparse.ArgumentParser(description="Summarize a quantum chemistry output file.")
    parser.add_argument("output_file", type=Path, help="Q-Chem output file to parse")
    parsed_args = parser.parse_args(args)

    parsed = QChemParser(parsed_args.output_file).parse()
    assistant = ChemistryAssistant(parsed)

    print(assistant.summarize())
    for recommendation in assistant.recommendations():
        print(f"- {recommendation}")


def zmat(argv=None):
    command, args = _resolve_args(argv, default_command="zmat")
    if command != "zmat":
        raise SystemExit("zmat expects a Q-Chem output file path")

    parser = argparse.ArgumentParser(description="Write a CFOUR-style ZMAT file from a Q-Chem output.")
    parser.add_argument("output_file", type=Path, help="Q-Chem output file containing the Z-matrix")
    parsed_args = parser.parse_args(args)

    writer = CfourZmatWriter(parsed_args.output_file)
    output_file = writer.write()
    print(f"Wrote {output_file}")


def main(argv=None):
    command, args = _resolve_args(argv)
    if command in {"summarize", "summary"}:
        summarize(args)
    elif command == "totalenergy":
        totalenergy(args)
    elif command == "zmat":
        zmat(args)
    else:
        raise SystemExit(f"unsupported command: {command}")


if __name__ == "__main__":
    main()
