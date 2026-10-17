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
