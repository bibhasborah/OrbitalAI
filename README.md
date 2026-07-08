# Q-AI

Q-AI is a lightweight toolkit for parsing and summarizing quantum chemistry output files.

## Features

- Parse Q-Chem output files and extract the total energy
- Identify the job type, electronic structure method, and basis set
- Produce a compact chemistry-focused summary with practical recommendations

## Quick start

```bash
pip install -e .

# Print the total energy
totalenergy examples/qchem/sample.out

# Generate a chemistry-oriented summary
chemistry-summary examples/qchem/sample.out
```

## Example

```python
from q_ai.parser.qchem import QChemParser
from q_ai.analysis.assistant import ChemistryAssistant

parser = QChemParser("examples/qchem/sample.out")
assistant = ChemistryAssistant(parser.parse())
print(assistant.summarize())
```
