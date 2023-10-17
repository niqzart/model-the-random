from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
from typing import Final, Literal

ROOT_FOLDER: Path = Path.cwd()
if ROOT_FOLDER.name == "app":
    ROOT_FOLDER = ROOT_FOLDER.parent

SAMPLE_SIZES: Final[tuple[int, ...]] = (10, 20, 50, 100, 200, 300)


def load_sequence_from_file() -> list[Decimal]:
    with (ROOT_FOLDER / "data" / "sequence.csv").open(encoding="utf-8") as f:
        return [Decimal(row[0]) for row in csv.reader(f)]


ConfidenceLevel = Literal["0.90", "0.95", "0.99"]


class SequenceSampleAnalyzer:
    confidence_to_coefficient: dict[ConfidenceLevel, Decimal] = {
        "0.90": Decimal("1.645"),
        "0.95": Decimal("1.960"),
        "0.99": Decimal("2.576"),
    }

    def __init__(self, sequence_sample: list[Decimal]) -> None:
        self.sequence_sample = sequence_sample
        self.size = len(sequence_sample)

        self.mean = self.calculate_mean()
        self.dispersion = self.calculate_dispersion()
        self.standard_deviation = self.calculate_standard_deviation()
        self.coefficient_of_variation = self.calculate_coefficient_of_variation()

        self.confidences: dict[ConfidenceLevel, Decimal] = {
            confidence_level: self.calculate_confidence_interval(confidence_level)
            for confidence_level in self.confidence_to_coefficient.keys()
        }

    def calculate_mean(self) -> Decimal:
        return Decimal(sum(self.sequence_sample) / len(self.sequence_sample))

    def calculate_dispersion(self) -> Decimal:
        return Decimal(
            sum((element - self.mean) ** 2 for element in self.sequence_sample)
            / (self.size - 1)
        )

    def calculate_standard_deviation(self) -> Decimal:
        return self.dispersion.sqrt()

    def calculate_coefficient_of_variation(self) -> Decimal:
        return self.standard_deviation / self.mean

    def calculate_confidence_interval(
        self, confidence_level: ConfidenceLevel
    ) -> Decimal:
        return (
            self.confidence_to_coefficient[confidence_level]
            * self.standard_deviation
            / Decimal(self.size).sqrt()
        )


class RelativeSequenceSampleAnalyzer(SequenceSampleAnalyzer):
    @classmethod
    def calculate_relative(cls, current: Decimal, base: Decimal) -> Decimal:
        return (abs(current - base) / base) * 100

    def __init__(
        self, sequence_sample: list[Decimal], relative_to: SequenceSampleAnalyzer
    ) -> None:
        super().__init__(sequence_sample)
        self.relative_to = relative_to

        self.relative_mean = self.calculate_relative(self.mean, relative_to.mean)
        self.relative_dispersion = self.calculate_relative(
            self.dispersion, relative_to.dispersion
        )
        self.relative_standard_deviation = self.calculate_relative(
            self.standard_deviation, relative_to.standard_deviation
        )
        self.relative_coefficient_of_variation = self.calculate_relative(
            self.coefficient_of_variation, relative_to.coefficient_of_variation
        )
        self.relative_confidences: dict[ConfidenceLevel, Decimal] = {
            confidence_level: self.calculate_relative(
                self.confidences[confidence_level],
                relative_to.confidences[confidence_level],
            )
            for confidence_level in self.confidence_to_coefficient.keys()
        }


if __name__ == "__main__":
    full_sequence = load_sequence_from_file()
    if len(full_sequence) != SAMPLE_SIZES[-1]:
        raise ValueError(f"Sequence should be {SAMPLE_SIZES[-1]} numbers")

    full_analyzer = SequenceSampleAnalyzer(full_sequence)
    for sample_size in SAMPLE_SIZES[:-1]:
        analyzer = RelativeSequenceSampleAnalyzer(
            full_sequence[:sample_size], full_analyzer
        )
        print(
            analyzer.size,
            analyzer.mean,
            analyzer.relative_mean,
            analyzer.dispersion,
            analyzer.relative_dispersion,
            analyzer.standard_deviation,
            analyzer.relative_standard_deviation,
            analyzer.coefficient_of_variation,
            analyzer.relative_coefficient_of_variation,
            analyzer.confidences,
            analyzer.relative_confidences,
        )
    print(
        full_analyzer.size,
        full_analyzer.mean,
        full_analyzer.dispersion,
        full_analyzer.standard_deviation,
        full_analyzer.coefficient_of_variation,
        full_analyzer.confidences,
    )
