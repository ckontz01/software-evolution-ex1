# Commit 08 — Recorded AI architecture and its evaluation

**Student B · 2026-10-21 · 28 complete files · 2 full code/configuration listings**

Source snapshot: `f32e6e831f976eed8bf01faa1d66dbdc34bc49c7`. Dates are planned work sessions; make the commit when you actually import and review this packet.

## What to understand

Read the preserved AI prompt and actual response; explain the 18-module proposal, complete class coverage and its evaluation on the same populations as the baselines.

## Apply this packet

Set `HANDOFF_DIR` to your extracted student bundle and `TEACHER_REPO` to the teacher checkout. Pull the preceding commit first. Commands below use the `guava-study` layout explained in the main map.

```bash
git -C "$TEACHER_REPO" pull --ff-only origin guava-assignment
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/08-b-ai-evaluation" --target "$TEACHER_REPO" --subdir guava-study
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/08-b-ai-evaluation" --target "$TEACHER_REPO" --subdir guava-study --apply
cd "$TEACHER_REPO/guava-study"
```

For commit 01, create the shared branch as shown in the main map; its remote branch does not exist until the first push, so omit that first pull.

## Checks before the commit

Run these in the cumulative study directory after applying the packet. For packet 01, first create the Python environment and install the locked requirements as shown in the main map:

```bash
```

Stage and inspect only this packet, then use your own Git identity:

```bash
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/08-b-ai-evaluation" --target "$TEACHER_REPO" --subdir guava-study --apply --stage
git -C "$TEACHER_REPO" diff --cached --stat
git -C "$TEACHER_REPO" diff --cached
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/08-b-ai-evaluation" --target "$TEACHER_REPO" --subdir guava-study --check-staged
git -C "$TEACHER_REPO" commit -m 'import: add recorded AI recovery and matching-graph evaluation (AI-assisted preparation)'
git -C "$TEACHER_REPO" push -u origin guava-assignment
```

Add a commit-message paragraph describing the checks you actually performed and anything you found. The import message identifies the prepared source; it does not claim you originally wrote every line.

## Further review checks

The following are useful for learning or final verification. Commands marked as writing evidence belong in a disposable copy, so the next packet still matches the frozen source. These are not additional canonical experiments.

Verify preserved AI prompt/input hashes and recompute metrics against current matching populations.

```bash
python scripts/evaluate_ai.py
```

**Where:** disposable cumulative checkout, preserving immutable packet payloads. **Writes:** rewrites derived results/ai files; use disposable cumulative checkout.

## Every file to push

All files below are present under this packet's `payload/` directory in the complete student download. Paths are relative to the study directory.

| File | Bytes | Content |
|---|---:|---|
| `docs/ai_reflection.md` | 13,829 | documentation or tool provenance |
| `results/ai/activity.json` | 6,035 | recorded evidence |
| `results/ai/architecture.json` | 36,985 | recorded evidence |
| `results/ai/assignment.csv` | 33,815 | recorded evidence |
| `results/ai/comparisons.csv` | 946 | recorded evidence |
| `results/ai/evaluation.json` | 1,577 | recorded evidence |
| `results/ai/experiment.json` | 2,439 | recorded evidence |
| `results/ai/initial_hypothesis.md` | 3,961 | recorded evidence |
| `results/ai/inputs/classes.csv` | 80,871 | recorded evidence |
| `results/ai/inputs/dependencies.csv` | 224,223 | recorded evidence |
| `results/ai/inputs/package_counts.json` | 629 | recorded evidence |
| `results/ai/inputs/package_dependencies.csv` | 3,465 | recorded evidence |
| `results/ai/inputs/package_documentation.txt` | 24,048 | recorded evidence |
| `results/ai/launch_message.txt` | 723 | recorded evidence |
| `results/ai/metrics.json` | 38,912 | recorded evidence |
| `results/ai/partition_comparisons.json` | 6,012 | recorded evidence |
| `results/ai/prompt.txt` | 3,536 | recorded evidence |
| `results/ai/quality_full/metrics_summary.csv` | 418 | recorded evidence |
| `results/ai/quality_full/per_cluster.csv` | 991 | recorded evidence |
| `results/ai/quality_full/per_pair.csv` | 7,952 | recorded evidence |
| `results/ai/quality_retained/metrics_summary.csv` | 430 | recorded evidence |
| `results/ai/quality_retained/per_cluster.csv` | 1,000 | recorded evidence |
| `results/ai/quality_retained/per_pair.csv` | 7,834 | recorded evidence |
| `results/ai/response.md` | 27,050 | recorded evidence |
| `results/ai/retained_metrics.json` | 38,815 | recorded evidence |
| `results/ai/source_graph_provenance.json` | 4,672 | recorded evidence |
| `scripts/evaluate_ai.py` | 6,521 | Full code below |
| `scripts/prepare_ai_inputs.py` | 8,730 | Full code below |

The machine-readable `packet.json` pins every file's SHA-256 and Git blob. Binary JAR/PDF/ZIP files and large evidence files are supplied as their exact original bytes in the payload, rather than as text pasted into this guide.

## Whole code

The following are complete files, with no omitted functions. Use the payload for copying so file bytes, line endings and original licences stay intact.

### scripts/evaluate_ai.py

SHA-256: `aa17ed9874fd57d10fd9fcf225d62a6f3ad13a5f11dcc7592d6c8bd55d82ac4a` · 6,521 bytes

<!-- FULL_SOURCE scripts/evaluate_ai.py aa17ed9874fd57d10fd9fcf225d62a6f3ad13a5f11dcc7592d6c8bd55d82ac4a -->
```python
#!/usr/bin/env python3
"""Score the recorded AI partition only after its blind recovery is complete."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evolution.graph import read_csv, read_graph, write_csv, write_json, sha256
from evolution.metrics import evaluate_partition, write_metric_tables
from evolution.mojofm import compare_mojofm
from evolution.study import load_partition


def main() -> None:
    directory = ROOT / 'results/ai'
    record = json.loads((directory / 'experiment.json').read_text())
    config = json.loads((ROOT / 'config/analysis.json').read_text())
    manifest = json.loads((ROOT / 'config/versions.json').read_text())
    version = record['version']
    if version != manifest['versions'][-1]['version']:
        raise ValueError('Recorded AI response does not target the last selected release')
    if sha256(ROOT / record['prompt_file']) != record['prompt_sha256']:
        raise ValueError('Recorded prompt changed')
    for item in record['input_files']:
        if sha256(ROOT / item['path']) != item['sha256']:
            raise ValueError(f'AI evidence changed: {item["path"]}')
    for item in record.get('additional_prompt_files', []):
        if sha256(ROOT / item['path']) != item['sha256']:
            raise ValueError(f'Additional prompt changed: {item["path"]}')
    source_provenance = directory / 'source_graph_provenance.json'
    if sha256(source_provenance) != record['input_provenance']['graph_provenance_sha256']:
        raise ValueError('Recorded source graph provenance changed')
    for filename in ('classes.csv', 'dependencies.csv'):
        if sha256(directory / 'inputs' / filename) != sha256(ROOT / 'data/graphs' / version / filename):
            raise ValueError(f'Current graph no longer matches the recorded AI input: {filename}')
    graph = read_graph(ROOT / 'data/graphs' / version)
    assignment = load_partition(directory / 'assignment.csv')
    metrics = evaluate_partition(graph.nodes, graph.edges, assignment)
    architecture = json.loads((directory / 'architecture.json').read_text())
    declared = {item['id']: item['class_count'] for item in architecture['modules']}
    if declared != dict(Counter(assignment.values())):
        raise ValueError('AI module declaration counts disagree with actual membership')
    # The archived retained-class manifest is authoritative for comparison scope.
    retained = {r['class'] for r in read_csv(ROOT / 'results/versions' / version / 'retained_classes.csv')}
    filtered = graph.without(set(graph.nodes) - retained)
    projected = {n: assignment[n] for n in filtered.nodes}
    retained_metrics = evaluate_partition(filtered.nodes, filtered.edges, projected)
    write_json(directory / 'metrics.json', metrics)
    write_json(directory / 'retained_metrics.json', retained_metrics)
    write_metric_tables(metrics, directory / 'quality_full')
    write_metric_tables(retained_metrics, directory / 'quality_retained')
    comparisons = []
    details = []
    for condition in ('A1', 'A2', 'A3', 'A4'):
        current = filtered if condition in ('A2', 'A4') else graph
        baseline = load_partition(ROOT / 'results/versions' / version / (condition + '.csv'))
        base_metrics = evaluate_partition(current.nodes, current.edges, baseline)
        ai = projected if current is filtered else assignment
        ai_metrics = retained_metrics if current is filtered else metrics
        forward, reverse = compare_mojofm(ai, baseline), compare_mojofm(baseline, ai)
        comparisons.append({'condition': condition, 'graph': 'retained' if current is filtered else 'full',
                            'n_nodes': len(current.nodes), 'n_edges': len(current.edges),
                            'baseline_mq': base_metrics['mq'], 'ai_mq': ai_metrics['mq'],
                            'mojofm_ai_to_baseline': forward['score'],
                            'mojofm_baseline_to_ai': reverse['score'],
                            'mojo_distance_ai_to_baseline': forward['distance'],
                            'mojo_distance_baseline_to_ai': reverse['distance'],
                            'mojo_max_distance_ai_to_baseline': forward['max_distance'],
                            'mojo_max_distance_baseline_to_ai': reverse['max_distance'],
                            'node_universe_sha256': hashlib.sha256(('\n'.join(sorted(current.nodes)) + '\n').encode()).hexdigest()})
        details.append({'comparison': comparisons[-1], 'ai_to_baseline': forward, 'baseline_to_ai': reverse})
    write_csv(directory / 'comparisons.csv', comparisons)
    write_json(directory / 'partition_comparisons.json', {'version': version, 'comparisons': details})
    outputs = ['initial_hypothesis.md', 'assignment.csv', 'architecture.json', 'response.md', 'activity.json']
    if not all((directory / name).is_file() for name in outputs):
        raise ValueError('Incomplete recorded AI response')
    write_json(directory / 'evaluation.json', {'version': version, 'status': 'passed',
               'study_revision': config['study_revision'],
               'source_experiment_revision': record['study_revision'],
               'evaluation_of_preserved_assignment': True,
               'config_sha256': sha256(ROOT / 'config/analysis.json'),
               'manifest_sha256': sha256(ROOT / 'config/versions.json'),
               'source_graph_provenance_file': str(source_provenance.relative_to(ROOT)),
               'source_graph_provenance_sha256': sha256(source_provenance),
               'current_graph_provenance_sha256': sha256(ROOT / 'data/graphs' / version / 'provenance.json'),
               'classes_assigned_exactly_once': len(assignment), 'modules': len(declared),
               'external_or_invented_classes': 0, 'input_hashes_verified': True,
               'output_sha256': {name: sha256(directory / name) for name in outputs},
               'metric_scope': 'Every comparison uses identical class and edge sets; retained AI assignment is a projection, not a new AI recovery.',
               'quality_claim': 'MoJoFM in both directions measures partition agreement, not accuracy. No validated intended-architecture ground truth is available.'})
    print(json.dumps({'version': version, 'modules': len(declared), 'full_mq': metrics['mq'], 'retained_mq': retained_metrics['mq'], 'comparisons': comparisons}, indent=2))


if __name__ == '__main__':
    main()
```
<!-- END_FULL_SOURCE scripts/evaluate_ai.py -->

### scripts/prepare_ai_inputs.py

SHA-256: `f55a1bd09e5e0ba51cc39f15e3e9fb74247d2d494c28780be068a7a405d1d709` · 8,730 bytes

<!-- FULL_SOURCE scripts/prepare_ai_inputs.py f55a1bd09e5e0ba51cc39f15e3e9fb74247d2d494c28780be068a7a405d1d709 -->
```python
#!/usr/bin/env python3
"""Prepare reproducible evidence for one fresh, blinded AI recovery session.

This only prepares evidence. An actual independent AI session must produce the
architecture; this script never fabricates a model response or partition.
"""
from collections import Counter
import argparse
import json
from pathlib import Path
import shutil
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evolution.graph import read_csv, sha256, write_csv, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'results/ai')
    args = parser.parse_args()
    directory = args.output.resolve()
    if (directory / 'assignment.csv').exists():
        raise ValueError('A completed response already exists; use a new --output directory')
    row = json.loads((ROOT / 'config/versions.json').read_text())['versions'][-1]
    version = row['version']
    graph = ROOT / 'data/graphs' / version
    classes, edges = read_csv(graph / 'classes.csv'), read_csv(graph / 'dependencies.csv')
    inputs = directory / 'inputs'
    inputs.mkdir(parents=True, exist_ok=True)
    for name in ('classes.csv', 'dependencies.csv'):
        shutil.copyfile(graph / name, inputs / name)
    packages = {r['class']: r['package'] for r in classes}
    write_json(inputs / 'package_counts.json', dict(sorted(Counter(packages.values()).items())))
    counts = Counter((packages[r['source']], packages[r['target']]) for r in edges)
    write_csv(inputs / 'package_dependencies.csv',
              [{'source_package': a, 'target_package': b, 'dependencies': count}
               for (a, b), count in sorted(counts.items())])
    source = ROOT / row['sources_path']
    if sha256(source) != row['sources_sha256']:
        raise ValueError('Source JAR does not match pinned release')
    with ZipFile(source) as archive:
        names = set(archive.namelist())
        documents = []
        for package in sorted(set(packages.values())):
            name = package.replace('.', '/') + '/package-info.java'
            if name in names:
                documents.append(f'===== {name} =====\n' + archive.read(name).decode('utf-8') + '\n')
    (inputs / 'package_documentation.txt').write_text('\n'.join(documents), encoding='utf-8')
    relative = directory.relative_to(ROOT).as_posix()
    prompt = f'''Recover a maintainable conceptual module architecture for the latest selected Guava JRE release, {version}, from the supplied evidence. This is an actual recorded AI architecture-recovery experiment for EPL484 Software Evolution. You are a fresh AI reviewer and must not inspect any ACDC/KMeans partitions, UE decisions, metric outcomes, reports, or other experiment outputs.

Use only the following files under {relative}/inputs (all from the same pinned release): classes.csv ({len(classes)} canonical outer types), dependencies.csv ({len(edges)} binary directed internal class dependencies), package_counts.json, package_dependencies.csv, and package_documentation.txt (unmodified package documentation from the matching source JAR). The primary dependencies are the instructor DependencyExtractor relationships. External libraries have already been excluded and inner/anonymous classes merged. The inventory includes all owned types, including isolated classes and annotation declarations; annotation applications are not edges in this graph. Both com.google.common and Guava-owned com.google.thirdparty.publicsuffix are in scope. A dependency points from a class using a type/member to the class being used. Package declarations and documentation are evidence, not a validated intended architecture. Do not browse external sources or inspect other project files. You may use Python to read and summarize only these inputs and produce the requested outputs.

First inspect classes.csv and package_counts.json only. Record a concise initial architecture hypothesis in {relative}/initial_hypothesis.md before reading dependency/documentation inputs. This hypothesis is qualitative, not a second finalized architecture. Then read the remaining evidence and refine the hypothesis into ONE complete final class partition. Select a practical number of named responsibility modules; do not target a numeric clustering metric. Classes in one package may be split if responsibility boundaries and dependency evidence justify it. Preserve isolated types. Give every supplied class exactly one module and invent no classes. Do not place a class in multiple modules, including utilities.

Write these outputs under {relative} only:
1. assignment.csv with columns class,cluster, containing every supplied class exactly once. Use semantic stable cluster IDs.
2. architecture.json with schema_version, subject.release, modules (id, name, responsibility, exact class_count, boundary_rationale), cross_module_observations, changes_from_initial_hypothesis, and limitations. Cite concrete class/package relationships and graph counts where relevant, separating interpretation from observation.
3. response.md: complete final explanation, including how additional evidence changed or confirmed the names-only hypothesis; package-structure bias; confidence limits; and which intended-design claims need maintainer validation. Do not claim superiority or architectural accuracy without ground truth. Explain how the proposal helps a human understand Guava.
4. activity.json: exact input paths read, tool/method summary, model identity available from your runtime (do not invent unavailable identifiers), and confirmation that baseline partitions and numeric quality scores were not consulted.

Validate partition coverage against classes.csv. Do not compute MQ/cohesion/coupling or compare with baseline algorithms; the coordinator evaluates afterward on matching graph scopes. Leave unrelated files untouched. No subdelegation is needed for this small controlled experiment.
'''
    (directory / 'prompt.txt').write_text(prompt, encoding='utf-8')
    launch = f'''Working directory {ROOT}. This is a fresh controlled AI architecture-recovery experiment. Your exact task is the full contents of {relative}/prompt.txt. Read that file first and follow it strictly. Read only that prompt and the listed {relative}/inputs evidence; do not inspect any other project data, results, code, baseline architectures, UE decisions or numeric quality scores. First save the initial names-only hypothesis, then inspect the remaining evidence and produce the specified final outputs. Your launch identity is GPT-6 Astra Pro as inherited. The launcher supplies no algorithm outcomes. Complete the recovery now; an independent reviewer evaluates afterward.'''
    (directory / 'launch_message.txt').write_text(launch + '\n', encoding='utf-8')
    write_json(directory / 'experiment.json', {
        'schema_version': 2, 'study_revision': 'v2_instructor_graph_distinct_families',
        'version': version, 'model': 'ChatGPT GPT-6 Astra Pro (fresh delegated session; no seed control exposed)',
        'prompt_file': f'{relative}/prompt.txt', 'prompt_sha256': sha256(directory / 'prompt.txt'),
        'input_files': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha256(p), 'bytes': p.stat().st_size}
                        for p in sorted(inputs.iterdir())],
        'assignment_file': f'{relative}/assignment.csv', 'architecture_file': f'{relative}/architecture.json',
        'output_file': f'{relative}/response.md',
        'additional_prompt_files': [{'path': f'{relative}/launch_message.txt',
                                     'sha256': sha256(directory / 'launch_message.txt'), 'sequence': 1}],
        'protocol': 'Initial qualitative names-only hypothesis, followed by one finalized evidence-informed partition. Fresh session without prior-turn history. Coordinator evaluates after completion.',
        'input_provenance': {'sources_jar_sha256': row['sources_sha256'],
                             'graph_provenance_sha256': sha256(graph / 'provenance.json')},
        'notes': ['Names and package documentation are allowed AI evidence; structural algorithms receive graph features only. This information asymmetry prevents a controlled same-input superiority claim.',
                  'A fresh session still has general pretrained knowledge. Hidden runtime instructions and model nondeterminism cannot be fully reproduced.',
                  'Original revision AI output is preserved in the original Git commit, not reused as this response.']})
    print(json.dumps({'version': version, 'classes': len(classes), 'edges': len(edges), 'output': relative}))


if __name__ == '__main__':
    main()
```
<!-- END_FULL_SOURCE scripts/prepare_ai_inputs.py -->
