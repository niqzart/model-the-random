from __future__ import annotations

import csv
from collections import deque
from collections.abc import Callable, Iterable
from decimal import Decimal
from math import ceil
from pathlib import Path
from random import random, seed
from typing import IO, Any, Final, Literal

from matplotlib import pyplot as plt

ROOT_FOLDER: Path = Path.cwd()
if ROOT_FOLDER.name == "app":
    ROOT_FOLDER = ROOT_FOLDER.parent

EPSILON: Decimal = Decimal("0.0001")
SAMPLE_SIZES: Final[tuple[int, ...]] = (10, 20, 50, 100, 200, 300)


def load_sequence_from_file() -> list[Decimal]:
    with (ROOT_FOLDER / "data" / "sequence.csv").open(encoding="utf-8") as f:
        return [Decimal(row[0]) for row in csv.reader(f)]


def plot_line_graph(sequence_of_floats: list[Any], name: str) -> None:
    plt.figure(figsize=(10, 5))
    plt.plot(sequence_of_floats)
    plt.xlim(0, len(sequence_of_floats))
    plt.xlabel("Number")
    plt.ylabel("Value")
    plt.title("Plot")
    plt.savefig(ROOT_FOLDER / "out" / f"{name}.png")
    plt.cla()


def plot_histogram(sequence_of_floats: list[float], name: str) -> None:
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
    plt.savefig(ROOT_FOLDER / "out" / f"{name}.png")
    plt.cla()


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

    def calculate_autocovariation(self, shift: int) -> Decimal:
        rotated = deque(self.sequence_sample, self.size)
        rotated.rotate(-shift)
        return Decimal(
            sum(
                (normal - self.mean) * (shifted - self.mean)
                for normal, shifted in zip(self.sequence_sample, rotated)
            )
        )

    def calculate_autocorrelation(self, shift: int) -> Decimal:
        return self.calculate_autocovariation(shift) / self.dispersion / (self.size - 1)

    def calculate_correlation(self, other: SequenceSampleAnalyzer) -> Decimal:
        return Decimal(
            sum(
                (a - self.mean) * (b - other.mean)
                for a, b in zip(self.sequence_sample, other.sequence_sample)
            )
            / Decimal(
                self.dispersion * other.dispersion * (self.size - 1) * (other.size - 1)
            ).sqrt()
        )


def calculate_relative(current: Decimal, base: Decimal) -> Decimal:
    return Decimal((abs(current - base) / abs(base)) * 100)


class RelativeSequenceSampleAnalyzer(SequenceSampleAnalyzer):
    def __init__(
        self, sequence_sample: list[Decimal], relative_to: SequenceSampleAnalyzer
    ) -> None:
        super().__init__(sequence_sample)
        self.relative_to = relative_to

        self.relative_mean = calculate_relative(self.mean, relative_to.mean)
        self.relative_dispersion = calculate_relative(
            self.dispersion, relative_to.dispersion
        )
        self.relative_standard_deviation = calculate_relative(
            self.standard_deviation, relative_to.standard_deviation
        )
        self.relative_coefficient_of_variation = calculate_relative(
            self.coefficient_of_variation, relative_to.coefficient_of_variation
        )
        self.relative_confidences: dict[ConfidenceLevel, Decimal] = {
            confidence_level: calculate_relative(
                self.confidences[confidence_level],
                relative_to.confidences[confidence_level],
            )
            for confidence_level in self.confidence_to_coefficient.keys()
        }


class BaseWriter:
    def __init__(self, f: IO[str]) -> None:
        self.writer = csv.writer(f, delimiter=",", lineterminator="\n")

    def writerow(self, row: Iterable[Any]) -> None:
        self.writer.writerow(row)


class Table1Writer(BaseWriter):
    def __init__(
        self,
        f: IO[str],
        partial_analyzers: list[RelativeSequenceSampleAnalyzer],
        full_analyzer: SequenceSampleAnalyzer,
    ) -> None:
        super().__init__(f)
        self.partial_analyzers = partial_analyzers
        self.all_analyzers: tuple[SequenceSampleAnalyzer, ...] = (
            *partial_analyzers,
            full_analyzer,
        )

    def write_from_all(self, accessor: Callable[[SequenceSampleAnalyzer], Any]) -> None:
        self.writerow([accessor(analyzer) for analyzer in self.all_analyzers])

    def write_from_partial(
        self,
        accessor: Callable[[RelativeSequenceSampleAnalyzer], Any],
    ) -> None:
        self.writerow([accessor(analyzer) for analyzer in self.partial_analyzers])


class Table2Writer(BaseWriter):
    def __init__(
        self,
        f: IO[str],
        analyzers: list[RelativeSequenceSampleAnalyzer],
    ) -> None:
        super().__init__(f)
        self.analyzers = analyzers

    def write_from_all(
        self, accessor: Callable[[RelativeSequenceSampleAnalyzer], Any]
    ) -> None:
        self.writerow([accessor(analyzer) for analyzer in self.analyzers])


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


def save_table2_to_csv(analyzers: list[RelativeSequenceSampleAnalyzer]) -> None:
    with (ROOT_FOLDER / "out" / "table2.csv").open("w", encoding="utf-8") as f:
        writer = Table2Writer(f, analyzers)
        for accessor in (
            lambda analyzer: analyzer.size,
            lambda analyzer: analyzer.mean,
            lambda analyzer: analyzer.relative_mean,
            lambda analyzer: analyzer.confidences["0.90"],
            lambda analyzer: analyzer.relative_confidences["0.90"],
            lambda analyzer: analyzer.confidences["0.95"],
            lambda analyzer: analyzer.relative_confidences["0.95"],
            lambda analyzer: analyzer.confidences["0.99"],
            lambda analyzer: analyzer.relative_confidences["0.99"],
            lambda analyzer: analyzer.dispersion,
            lambda analyzer: analyzer.relative_dispersion,
            lambda analyzer: analyzer.standard_deviation,
            lambda analyzer: analyzer.relative_standard_deviation,
            lambda analyzer: analyzer.coefficient_of_variation,
            lambda analyzer: analyzer.relative_coefficient_of_variation,
        ):
            writer.write_from_all(accessor)


def save_table3_to_csv(*data: list[Decimal]) -> None:
    with (ROOT_FOLDER / "out" / "table3.csv").open("w", encoding="utf-8") as f:
        writer = BaseWriter(f)
        writer.writerow(i + 1 for i in range(len(data[0])))
        for autocorrelation_coefficients in data:
            writer.writerow(coefficient for coefficient in autocorrelation_coefficients)


def generate_erlang(a: Decimal, k: int) -> Decimal:
    return Decimal(-(1 / a) * sum(Decimal(random()).ln() for _ in range(k)))


if __name__ == "__main__":
    # setup
    seed(53)
    (ROOT_FOLDER / "out").mkdir(exist_ok=True)
    full_sequence = load_sequence_from_file()
    if len(full_sequence) != SAMPLE_SIZES[-1]:
        raise ValueError(f"Sequence should be {SAMPLE_SIZES[-1]} numbers")

    # plot source sequence
    sequence_of_floats = [float(element) for element in full_sequence]
    plot_line_graph(sequence_of_floats, "source-line-graph")
    plot_histogram(sequence_of_floats, "source-histogram")

    # analyze source sequence
    full_analyzer: SequenceSampleAnalyzer = SequenceSampleAnalyzer(full_sequence)
    partial_analyzers: list[RelativeSequenceSampleAnalyzer] = [
        RelativeSequenceSampleAnalyzer(full_sequence[:sample_size], full_analyzer)
        for sample_size in SAMPLE_SIZES[:-1]
    ]
    save_table1_to_csv(partial_analyzers, full_analyzer)

    # analyze autocorrelation for source sequence
    source_autocorrelation = [
        full_analyzer.calculate_autocorrelation(i) for i in range(1, 11)
    ]
    plot_line_graph(
        [None] + [float(e) for e in source_autocorrelation], "autocorrelation"
    )

    # detect distribution type & generate new sequence
    variation = full_analyzer.coefficient_of_variation
    if variation < EPSILON:  # TODO deterministic
        print("Detected deterministic variable")
    elif variation < 1 - EPSILON:  # erlang distribution
        k_full = 1 / (variation**2)
        k = ceil(k_full)
        a = k / full_analyzer.mean
        print(f"Detected erlang-{k} distribution")
        print(f"Parameter k: {k_full}")
        print(f"Parameter a: {a}")
        generated_sequence = [generate_erlang(a, k) for _ in range(300)]
    elif variation < 1 + EPSILON:  # TODO exponential
        print("Detected exponential distribution")
    else:  # TODO hyperexponential
        print("Detected hyperexponential distribution")

    # plot generated sequence
    sequence_of_floats = [float(element) for element in generated_sequence]
    plot_line_graph(sequence_of_floats, "result-line-graph")
    plot_histogram(sequence_of_floats, "result-histogram")

    # analyze generated sequence
    source_analyzers = (*partial_analyzers, full_analyzer)
    analyzers: list[RelativeSequenceSampleAnalyzer] = [
        RelativeSequenceSampleAnalyzer(
            generated_sequence[:sample_size], source_analyzers[i]
        )
        for i, sample_size in enumerate(SAMPLE_SIZES)
    ]
    save_table2_to_csv(analyzers)

    # analyze autocorrelation for generated sequence
    generated_autocorrelation = [
        analyzers[-1].calculate_autocorrelation(i) for i in range(1, 11)
    ]
    relative_autocorrelation = [
        calculate_relative(generated, source)
        for source, generated in zip(source_autocorrelation, generated_autocorrelation)
    ]
    save_table3_to_csv(
        source_autocorrelation,
        generated_autocorrelation,
        relative_autocorrelation,
    )

    # source to generated correlation
    print(
        "Correlation from generator:",
        full_analyzer.calculate_correlation(analyzers[-1]),
    )
