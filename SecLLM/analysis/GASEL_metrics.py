from __future__ import annotations

from typing import TextIO

import csv
from collections import defaultdict

import click
import rich
import rich.table
import pandas as pd

@click.command()
@click.argument('SAMPLE_CSV', type=click.File())
@click.option('--keep-unscanned/--omit-unscanned', default=True, help="Includi o escludi i campioni con cluster 'NotScannedByUs'")
def calculate_precision_recall(sample_csv: TextIO, keep_unscanned: bool) -> None:
    """Calcola precisione e recall per i campioni di validazione manuale nel file SAMPLE_CSV."""

    print(keep_unscanned, "\n", sample_csv)
    
    # Leggi i campioni direttamente con il delimitatore ','
    #try:
    #    samples = {_transform_sample(s) for s in csv.DictReader(sample_csv, delimiter=',') if s['smell_id']}
    #except Exception as e:
    samples = {_transform_sample(s) for s in csv.DictReader(sample_csv, delimiter=';') if s['smell_id']}

    detectors = {detector for _, _, detector, *_ in samples}

    smell_type_to_detector_to_samples: dict[str, dict[str, set[tuple[str, bool]]]] = defaultdict(lambda: defaultdict(set))
    for sample in samples:
        smell_type, cluster_name, detector, smell_id, true_positive = sample
        if detector not in ('scansible', 'glitch', 'slac', 'secLLM'):
            continue
        if not keep_unscanned and cluster_name == 'NotScannedByUs':
            continue
        smell_type_to_detector_to_samples[smell_type][detector].add((smell_id, true_positive))

    # smell_type -> (detector -> (precision, recall))
    metrics: dict[str, dict[str, tuple[float, float]]] = defaultdict(dict)
    smell_counts: dict[str, tuple[int, int, int]] = {}

    for smell_type, detector_to_samples in smell_type_to_detector_to_samples.items():
        num_overall = sum(len(detector_samples) for detector_samples in detector_to_samples.values())
        num_overall_unique = len({sample_id for detector_samples in detector_to_samples.values() for sample_id, *_ in detector_samples})
        num_overall_tp = len({sample_id for detector_samples in detector_to_samples.values() for sample_id, true_positive in detector_samples if true_positive})

        smell_counts[smell_type] = (num_overall, num_overall_unique, num_overall_tp)

        for detector, detector_samples in detector_to_samples.items():
            tp = len({sample_id for sample_id, true_positive in detector_samples if true_positive})
            fp = len({sample_id for sample_id, true_positive in detector_samples if not true_positive})
            fn = num_overall_tp - tp

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            metrics[smell_type][detector] = (precision, recall)
            if smell_type == 'AdminByDefault':
                print(f"detector: {detector} smell_type: {smell_type} tp: {tp} fp: {fp} fn: {fn} precision: {precision} recall: {recall}")

    # Genera la tabella dei risultati
    for smell_type, detector_to_metrics in sorted(metrics.items()):
        num_checked, num_unique, num_tp = smell_counts[smell_type]
        table = rich.table.Table('detector', title=f'{smell_type}: Precisione e recall per {num_tp} veri positivi su {num_checked} ({num_unique} unici) campioni controllati')
        table.add_column('precision', justify='right')
        table.add_column('recall', justify='right')

        max_precision = max(precision for precision, _ in detector_to_metrics.values())
        max_recall = max(recall for _, recall in detector_to_metrics.values())

        for detector in sorted(detector_to_metrics):
            precision, recall = detector_to_metrics[detector]
            table.add_row(
                detector,
                _render_percentage(precision, max_precision),
                _render_percentage(recall, max_recall))

        rich.print(table)


def _render_percentage(perc: float, max_perc: float) -> str:
    s = f'{perc * 100:2.2f}%'
    if perc == max_perc:
        return '[b]' + s
    return s


def _transform_sample(sample: dict[str, str]) -> tuple[str, str, str, str, bool]:
    sample_id = f'{sample["repo"]}/{sample["file_path"]}/{sample["smell_id"]}'
    return sample['smell_type'], sample['cluster_name'], sample['detector'], sample_id, sample['true_positive'].lower() == 'true'


if __name__ == '__main__':
    calculate_precision_recall()
