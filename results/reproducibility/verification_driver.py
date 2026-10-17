#!/usr/bin/env python3
"""Isolated fresh-clone verification; never writes the primary assignment repo."""
from __future__ import annotations
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

BASE = Path('/workspace/scratch/7500a23b5952')
CHECKOUT = BASE / 'verification_checkout'
EVIDENCE = BASE / 'verification_evidence'
FINAL_COMMIT = os.environ.get('VERIFICATION_FINAL_COMMIT', '29f46565515a45bdb233d2cbee6919aa3e8e49bf')
PDF_SHA256 = 'b60ef4483b957aa8cfc5d3d24d220d6ecf5a2e3cc479d63f82f03fa9b099801f'
JAVA = str(BASE / 'toolchain/jdk-17.0.20.1+1-jre/bin/java')
ENV = {**os.environ, 'EVOLUTION_JAVA': JAVA, 'LOKY_MAX_CPU_COUNT': '1'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def latest():
    os.environ.update({'EVOLUTION_JAVA': JAVA, 'LOKY_MAX_CPU_COUNT': '1'})
    sys.path.insert(0, str(CHECKOUT / 'src'))
    from evolution.extraction import extract_release
    from evolution.graph import read_graph, read_csv, write_csv, write_json
    from evolution.omnipresent import detect_omnipresent
    from evolution.study import _run_acdc, _run_kmeans, save_partition
    from evolution.metrics import evaluate_partition
    manifest = json.loads((CHECKOUT / 'config/versions.json').read_text())
    config = json.loads((CHECKOUT / 'config/analysis.json').read_text())
    row = manifest['versions'][-1]
    version = row['version']
    work = CHECKOUT / 'verification_work'
    graph_root = work / 'graphs'
    out = work / 'results' / version
    out.mkdir(parents=True, exist_ok=True)
    extract_release(row, graph_root, java=JAVA)
    graph = read_graph(graph_root / version)
    noise = detect_omnipresent(graph.nodes, read_csv(graph_root / version / 'member_dependencies.csv'),
                              usage_threshold=config['omnipresent']['usage_threshold'],
                              cardinality_threshold=config['omnipresent']['cardinality_threshold'])
    write_json(out / 'ue.json', noise.to_dict(include_dedications=True))
    write_csv(out / 'omnipresent.csv', [s.to_dict() for s in noise.scores])
    filtered = graph.without(noise.removed_classes)
    filtered.rsf(out / 'filtered.rsf')
    write_csv(out / 'retained_classes.csv', [{'class': n} for n in filtered.nodes], ['class'])
    universe = json.loads((CHECKOUT / 'data/graphs/feature_universe.json').read_text())
    for condition, current in [('A1', graph), ('A2', filtered), ('A3', graph), ('A4', filtered)]:
        if condition in ('A1', 'A2'):
            assignment, metadata = _run_acdc(current, out / (condition + '_run'), config, JAVA)
        else:
            assignment, metadata = _run_kmeans(current, universe, len(graph.nodes), config)
        save_partition(out / (condition + '.csv'), assignment)
        write_json(out / (condition + '_metrics.json'), evaluate_partition(current.nodes, current.edges, assignment))
        write_json(out / (condition + '_run.json'), metadata)
    pairs = []
    graph_files = ['classes.csv', 'dependencies.csv', 'dependencies_typed.csv', 'class_aliases.csv',
                   'extraction_counts.csv', 'member_dependencies.csv', 'unresolved_member_uses.csv',
                   'excluded_classes.csv', 'source_sizes.csv', 'full.rsf']
    for name in graph_files:
        pairs.append((CHECKOUT / 'data/graphs' / version / name, graph_root / version / name))
    for name in ['ue.json', 'omnipresent.csv', 'filtered.rsf', 'retained_classes.csv'] + [
            condition + suffix for condition in ('A1', 'A2', 'A3', 'A4') for suffix in ('.csv', '.rsf', '_metrics.json')]:
        pairs.append((CHECKOUT / 'results/versions' / version / name, out / name))
    comparisons = [{'archived': str(a.relative_to(CHECKOUT)), 'reproduced': str(b.relative_to(CHECKOUT)),
                    'archived_sha256': sha(a), 'reproduced_sha256': sha(b),
                    'byte_identical': a.read_bytes() == b.read_bytes()} for a, b in pairs]
    result = {'status': 'passed' if all(r['byte_identical'] for r in comparisons) else 'failed',
              'version': version, 'canonical_classes': len(graph.nodes), 'edges': len(graph.edges),
              'removed_classes': list(noise.removed_classes), 'retained_classes': len(filtered.nodes),
              'retained_edges': len(filtered.edges), 'byte_comparisons': comparisons,
              'comparison_count': len(comparisons),
              'excluded_from_byte_comparison': 'Execution metadata containing paths and elapsed time'}
    save(EVIDENCE / 'latest_reproduction.json', result)
    print(json.dumps({'status': result['status'], 'version': version, 'exact_file_comparisons': len(comparisons)}))
    return 0 if result['status'] == 'passed' else 1


def main():
    EVIDENCE.mkdir(exist_ok=True)
    if '--latest-only' in sys.argv:
        return latest()
    receipt = {
        'status': 'running', 'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'checkout': str(CHECKOUT), 'primary_repository_touched': False,
        'cloned_repository': 'https://github.com/ckontz01/software-evolution-ex1',
        'initial_clone_commit': '1112e94d36e9b7e49018790c1ae71ccdae6740f3',
        'clone_argv': ['git', 'clone', 'https://github.com/ckontz01/software-evolution-ex1', str(CHECKOUT)],
        'verification_start_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=CHECKOUT, text=True).strip(),
        'final_commit_expected': FINAL_COMMIT,
        'environment': {'python': sys.version, 'platform': platform.platform(),
                        'EVOLUTION_JAVA': JAVA, 'LOKY_MAX_CPU_COUNT': '1',
                        'packages': {p: importlib.metadata.version(p) for p in ('numpy', 'scipy', 'scikit-learn', 'matplotlib', 'reportlab')}},
        'runner_sha256': sha(__file__), 'commands': [],
    }
    receipt_path = EVIDENCE / 'receipt.json'
    commands = [
        ['git', 'fetch', 'origin', 'main'],
        ['git', 'merge', '--ff-only', FINAL_COMMIT],
        ['python3', 'scripts/unpack_data.py'],
        ['python3', 'scripts/fetch_tools.py'],
        ['python3', 'scripts/fetch_data.py', '--offline', '--verify-git'],
        ['python3', 'scripts/run_checks.py'],
        ['python3', 'scripts/validate_results.py'],
        ['python3', 'scripts/evaluate_ai.py'],
        ['python3', str(Path(__file__).resolve()), '--latest-only'],
    ]
    save(receipt_path, receipt)
    for index, command in enumerate(commands, 1):
        started = time.perf_counter()
        log = EVIDENCE / f'{index:02d}.log'
        print('RUN', ' '.join(command), flush=True)
        with log.open('w') as stream:
            done = subprocess.run(command, cwd=CHECKOUT, env=ENV, stdout=stream, stderr=subprocess.STDOUT)
        entry = {'argv': command, 'cwd': str(CHECKOUT), 'exit_code': done.returncode,
                 'elapsed_seconds': time.perf_counter() - started, 'log': str(log), 'log_sha256': sha(log)}
        receipt['commands'].append(entry)
        if index == 2 and done.returncode == 0:
            receipt['tested_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=CHECKOUT, text=True).strip()
        save(receipt_path, receipt)
        if done.returncode:
            receipt['status'] = 'failed'
            receipt['failed_command'] = command
            save(receipt_path, receipt)
            print('FAILED', log.read_text()[-6000:], flush=True)
            return done.returncode
        print('PASS', command[1], flush=True)
    receipt['final_commit_observed'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=CHECKOUT, text=True).strip()
    pdfs = [p for p in CHECKOUT.rglob('*.pdf') if '.git' not in p.parts and 'verification_work' not in p.parts]
    receipt['pdf_files'] = [{'path': str(p.relative_to(CHECKOUT)), 'sha256': sha(p)} for p in pdfs]
    receipt['expected_pdf_sha256'] = PDF_SHA256
    receipt['pdf_checksum_matched'] = any(p['sha256'] == PDF_SHA256 for p in receipt['pdf_files'])
    receipt['validation'] = json.loads((CHECKOUT / 'results/validation.json').read_text())['status']
    receipt['latest_reproduction'] = json.loads((EVIDENCE / 'latest_reproduction.json').read_text())
    receipt['status'] = 'passed' if receipt['final_commit_observed'] == FINAL_COMMIT and receipt['pdf_checksum_matched'] else 'failed'
    receipt['completed_at_utc'] = datetime.now(timezone.utc).isoformat()
    save(receipt_path, receipt)
    print(json.dumps({'status': receipt['status'], 'commit': receipt['final_commit_observed'],
                      'pdf_checksum_matched': receipt['pdf_checksum_matched'], 'receipt': str(receipt_path)}), flush=True)
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
