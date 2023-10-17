from __future__ import annotations

import csv
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import IO, Any, Final, Literal

from matplotlib import pyplot as plt

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


class Table1Writer:
    def __init__(
        self,
        f: IO[str],
        partial_analyzers: list[RelativeSequenceSampleAnalyzer],
        full_analyzer: SequenceSampleAnalyzer,
    ) -> None:
        self.writer = csv.writer(f, delimiter=",", lineterminator="\n")
        self.partial_analyzers = partial_analyzers
        self.all_analyzers: tuple[SequenceSampleAnalyzer, ...] = (
            *partial_analyzers,
            full_analyzer,
        )

    def write_from_all(self, accessor: Callable[[SequenceSampleAnalyzer], Any]) -> None:
        self.writer.writerow([accessor(analyzer) for analyzer in self.all_analyzers])

    def write_from_partial(
        self,
        accessor: Callable[[RelativeSequenceSampleAnalyzer], Any],
    ) -> None:
        self.writer.writerow(
            [accessor(analyzer) for analyzer in self.partial_analyzers]
        )


def save_table1_to_csv(
    partial_analyzers: list[RelativeSequenceSampleAnalyzer],
    full_analyzer: SequenceSampleAnalyzer,
) -> None:
    with (ROOT_FOLDER / "out" / "table1.csv").open("w", encoding="utf-8") as f:
        writer = Table1Writer(f, partial_analyzers, full_analyzer)

        writer.write_from_all(lambda analyzer: analyzer.size)

        writer.write_from_all(lambda analyzer: analyzer.mean)
        writer.write_from_partial(lambda analyzer: analyzer.relative_mean)

        for confidence_level in SequenceSampleAnalyzer.confidence_to_coefficient.keys():
            writer.write_from_all(
                lambda analyzer: analyzer.confidences[confidence_level]  # noqa: B023
            )
            writer.write_from_partial(
                lambda analyzer: analyzer.relative_confidences[
                    confidence_level  # noqa: B023
                ]
            )

        writer.write_from_all(lambda analyzer: analyzer.dispersion)
        writer.write_from_partial(lambda analyzer: analyzer.relative_dispersion)

        writer.write_from_all(lambda analyzer: analyzer.standard_deviation)
        writer.write_from_partial(lambda analyzer: analyzer.relative_standard_deviation)

        writer.write_from_all(lambda analyzer: analyzer.coefficient_of_variation)
        writer.write_from_partial(
            lambda analyzer: analyzer.relative_coefficient_of_variation
        )


if __name__ == "__main__":
    full_sequence = load_sequence_from_file()
    if len(full_sequence) != SAMPLE_SIZES[-1]:
        raise ValueError(f"Sequence should be {SAMPLE_SIZES[-1]} numbers")

    (ROOT_FOLDER / "out").mkdir(exist_ok=True)

    full_analyzer: SequenceSampleAnalyzer = SequenceSampleAnalyzer(full_sequence)
    partial_analyzers: list[RelativeSequenceSampleAnalyzer] = [
        RelativeSequenceSampleAnalyzer(full_sequence[:sample_size], full_analyzer)
        for sample_size in SAMPLE_SIZES[:-1]
    ]
    save_table1_to_csv(partial_analyzers, full_analyzer)

    sequence_of_floats = [float(element) for element in full_sequence]

    plt.figure(figsize=(10, 5))
    plt.plot(sequence_of_floats)
    plt.xlim(0, len(sequence_of_floats))
    plt.xlabel("Number")
    plt.ylabel("Value")
    plt.title("Plot")
    plt.savefig(ROOT_FOLDER / "out" / "line-graph.png")
    plt.cla()

    plt.hist(
        x=sequence_of_floats,
        bins="auto",
        rwidth=0.85,
        range=(0, max(sequence_of_floats)),
    )
    plt.grid(axis="y")
    plt.xlabel("Value")
    plt.ylabel("Count")
    plt.title("Histogram")
    plt.savefig(ROOT_FOLDER / "out" / "histogram.png")
