from decimal import Decimal
from pathlib import Path
from typing import Final

ROOT_FOLDER: Path = Path.cwd()
if ROOT_FOLDER.name == "app":
    ROOT_FOLDER = ROOT_FOLDER.parent

SAMPLE_SIZES: Final[tuple[int, ...]] = (10, 20, 50, 100, 200, 300)


def load_sequence_from_file() -> list[Decimal]:
    with (ROOT_FOLDER / "data" / "sequence.csv").open(encoding="utf-8") as f:
        return [Decimal(line) for line in f.read().strip().split("\n")]


def calculate_sample_mean(sequence: list[Decimal]) -> Decimal:
    return Decimal(sum(sequence) / len(sequence))


def calculate_sample_dispersion(
    sequence: list[Decimal], sample_mean: Decimal
) -> Decimal:
    normalized_sum = sum((element - sample_mean) ** 2 for element in sequence)
    return Decimal(normalized_sum / (len(sequence) - 1))


def calculate_sample_standard_deviation(sample_dispersion: Decimal) -> Decimal:
    return sample_dispersion.sqrt()


def calculate_sample_coefficient_of_variation(
    sample_mean: Decimal, sample_standard_deviation: Decimal
) -> Decimal:
    return sample_standard_deviation / sample_mean


confidence_to_coefficient: dict[Decimal, Decimal] = {
    Decimal(0.90): Decimal(1.645),
    Decimal(0.95): Decimal(1.960),
    Decimal(0.99): Decimal(2.576),
}


def calculate_confidence_interval(
    confidence_level: Decimal, sample_standard_deviation: Decimal, sample_size: int
) -> Decimal:
    return (
        confidence_to_coefficient[confidence_level]
        * sample_standard_deviation
        / Decimal(sample_size).sqrt()
    )


if __name__ == "__main__":
    full_sequence = load_sequence_from_file()
    if len(full_sequence) != SAMPLE_SIZES[-1]:
        raise ValueError(f"Sequence should be {SAMPLE_SIZES[-1]} numbers")

    for sample_size in SAMPLE_SIZES:
        sample_sequence = full_sequence[:sample_size]
        sample_mean = calculate_sample_mean(sample_sequence)
        sample_dispersion = calculate_sample_dispersion(sample_sequence, sample_mean)
        sample_standard_deviation = calculate_sample_standard_deviation(
            sample_dispersion
        )
        sample_coefficient_of_variation = calculate_sample_coefficient_of_variation(
            sample_mean, sample_standard_deviation
        )
        confidences = {
            confidence_level: calculate_confidence_interval(
                confidence_level, sample_standard_deviation, sample_size
            )
            for confidence_level in confidence_to_coefficient.keys()
        }
        print(
            sample_size,
            *confidences.values(),
        )
