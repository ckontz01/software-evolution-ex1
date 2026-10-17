#!/usr/bin/env python3
"""Run the paper-based JNode-UE replacement as a standalone explainable tool."""
import argparse
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evolution.graph import read_csv, write_csv, write_json
from evolution.omnipresent import detect_omnipresent

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classes', type=Path, required=True, help='Extractor classes.csv, with class column')
    parser.add_argument('--members', type=Path, required=True, help='Extractor member_dependencies.csv')
    parser.add_argument('--output', type=Path, required=True, help='New output directory')
    parser.add_argument('--usage-threshold', type=float, default=.85)
    parser.add_argument('--cardinality-threshold', type=float, default=.90)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new output directory to preserve any previous run')
    classes = [r['class'] for r in read_csv(args.classes)]
    rows = read_csv(args.members)
    started = time.perf_counter()
    result = detect_omnipresent(classes, rows, usage_threshold=args.usage_threshold,
                                cardinality_threshold=args.cardinality_threshold)
    seconds = time.perf_counter() - started
    args.output.mkdir(parents=True)
    write_json(args.output / 'ue.json', result.to_dict(include_dedications=True))
    write_csv(args.output / 'omnipresent.csv', [r.to_dict() for r in result.scores])
    write_csv(args.output / 'removed_classes.csv', [{'class': n} for n in result.removed_classes], ['class'])
    write_json(args.output / 'run.json', {'method': 'Yano and Matsuo2020 UE; not historical ComponentRank JNode',
                'classes_file': str(args.classes), 'members_file': str(args.members),
                'detector_seconds_excluding_csv_io': seconds, 'classes': len(classes),
                'removed': len(result.removed_classes)})
    print(f'JNode-UE: {len(result.removed_classes)} of {len(classes)} classes; {seconds:.6f}s detector-only')
