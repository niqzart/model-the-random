from pathlib import Path
from typing import Final

ROOT_FOLDER: Path = Path.cwd()
if ROOT_FOLDER.name == "app":
    ROOT_FOLDER = ROOT_FOLDER.parent

SAMPLE_SIZES: Final[tuple[int, ...]] = (10, 20, 50, 100, 200, 300)


def load_sequence_from_file() -> list[float]:
    with (ROOT_FOLDER / "data" / "sequence.csv").open(encoding="utf-8") as f:
        return [float(line) for line in f.read().strip().split("\n")]


if __name__ == "__main__":
    sequence = load_sequence_from_file()
    if len(sequence) == SAMPLE_SIZES[-1]:
        raise ValueError(f"Sequence should be {SAMPLE_SIZES[-1]} numbers")

    for sample_size in SAMPLE_SIZES:
        print(sequence[:sample_size])
