"""Reproducible Scientific Benchmark Runner.

Executes comparative experimental evaluations for:
- Experiment A: URL similarity only (Baseline A)
- Experiment B: URL + lexical/context matching (Baseline B)
- Experiment C: Semantic similarity only
- Experiment D: Proposed Hybrid model
- Experiment E: Proposed Hybrid model + Autonomous Remediation

Prints formatted research paper comparison table and exports reproducible metrics.
"""

import sys
import os
import argparse
import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.experiment_service import BenchmarkExperimentService
from backend.app.core.config import settings


def format_table(rows: list, headers: list) -> str:
    """Format rows and headers into a clean ASCII table."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))

    sep = "+" + "+".join(["-" * (w + 2) for w in widths]) + "+"
    header_str = "|" + "|".join([f" {headers[i].center(widths[i])} " for i in range(len(headers))]) + "|"

    data_lines = []
    for row in rows:
        line = "|" + "|".join([f" {str(row[i]).ljust(widths[i])} " for i in range(len(row))]) + "|"
        data_lines.append(line)

    return "\n".join([sep, header_str, sep] + data_lines + [sep])


async def main():
    parser = argparse.ArgumentParser(description="Run scientific link remediation experiments")
    parser.add_argument(
        "--mode",
        choices=["all", "baseline_url", "baseline_lexical", "semantic_only", "proposed_hybrid", "ablation"],
        default="all",
        help="Experiment mode to run",
    )
    parser.add_argument(
        "--dataset-version",
        default="v1.0",
        help="Benchmark dataset version",
    )
    parser.add_argument(
        "--output-file",
        default=None,
        help="Optional path to output comparison JSON",
    )
    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("INTELLIGENT LINK INTEGRITY MANAGEMENT & AUTONOMOUS REMEDIATION")
    print("SCIENTIFIC BENCHMARK EXPERIMENT RUNNER")
    print("=" * 80)
    print(f"Dataset Version: {args.dataset_version}")
    print(f"Timestamp:       {datetime.now(timezone.utc).isoformat()}")
    print("-" * 80)

    if args.mode == "all":
        print("\nExecuting comprehensive 4-method comparison on benchmark dataset...")
        comp = await BenchmarkExperimentService.run_comparative_benchmark()

        headers = ["Method", "Precision", "Recall", "F1", "Top-1", "Top-3", "MRR", "Repair Prec", "Repair Rate"]
        rows = []
        for r in comp["comparison_table"]:
            rows.append([
                r["method"],
                f"{r['precision']:.3f}",
                f"{r['recall']:.3f}",
                f"{r['f1']:.3f}",
                f"{r['top1']:.3f}",
                f"{r['top3']:.3f}",
                f"{r['mrr']:.3f}",
                f"{r['repair_precision']:.3f}",
                f"{r['repair_rate']:.3f}",
            ])

        print("\nEXPERIMENTAL RESULTS COMPARISON TABLE (Real computed numbers):")
        print(format_table(rows, headers))

        proposed = comp["runs"]["proposed_hybrid"]
        print("\nPROPOSED HYBRID MODEL DETAILED SUMMARY:")
        print(f"  • Total Benchmark Test Cases: {proposed['total_test_cases']}")
        print(f"  • Top-1 Retrieval Accuracy:   {proposed['retrieval_metrics']['top1_accuracy'] * 100:.1f}%")
        print(f"  • Top-3 Retrieval Accuracy:   {proposed['retrieval_metrics']['top3_accuracy'] * 100:.1f}%")
        print(f"  • Mean Reciprocal Rank (MRR): {proposed['retrieval_metrics']['mrr']:.4f}")
        print(f"  • Auto Repair Precision:      {proposed['remediation_metrics']['auto_repair_precision'] * 100:.1f}%")
        print(f"  • Auto Repair Rate:           {proposed['remediation_metrics']['auto_repair_rate'] * 100:.1f}%")
        print(f"  • Human Review Rate:          {proposed['remediation_metrics']['human_review_rate'] * 100:.1f}%")
        print(f"  • False Repair Rate:          {proposed['remediation_metrics']['false_repair_rate'] * 100:.1f}%")
        print(f"  • Average Case Latency:       {proposed['efficiency']['avg_case_latency_ms']:.1f} ms")
        print(f"  • Processing Throughput:      {proposed['efficiency']['throughput_links_per_min']:.1f} links/min")

        print("\nCONFIDENCE CALIBRATION ANALYSIS:")
        cal_headers = ["Confidence Range", "Cases", "Correct Top-1", "Accuracy %"]
        cal_rows = []
        for c in proposed["confidence_calibration"]:
            cal_rows.append([
                c["confidence_range"],
                str(c["total_cases"]),
                str(c["correct_recommendations"]),
                f"{c['accuracy_percentage']:.1f}%",
            ])
        print(format_table(cal_rows, cal_headers))

        out_path = args.output_file or str(settings.EXPERIMENTS_DIR / "comparison_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(comp, f, indent=2)
        print(f"\nSaved benchmark results to: {out_path}")

    elif args.mode == "ablation":
        print("\nRunning Feature Ablation Study across individual signal modalities...")
        features = [
            ("All Features (Proposed)", []),
            ("No Semantic Similarity", ["semantic_similarity"]),
            ("No URL Similarity", ["url_similarity"]),
            ("No Title Similarity", ["title_similarity"]),
            ("No Keyword Overlap", ["keyword_overlap"]),
            ("No Domain Matching", ["domain_score"]),
        ]

        abl_headers = ["Configuration", "Top-1 Acc", "Top-3 Acc", "MRR", "Repair Prec", "Delta Top-1"]
        base_res = await BenchmarkExperimentService.run_experiment(
            method="PROPOSED_HYBRID",
            disabled_features=[],
        )
        base_top1 = base_res["retrieval_metrics"]["top1_accuracy"]

        abl_rows = [[
            "All Features (Full Proposed)",
            f"{base_top1:.3f}",
            f"{base_res['retrieval_metrics']['top3_accuracy']:.3f}",
            f"{base_res['retrieval_metrics']['mrr']:.3f}",
            f"{base_res['remediation_metrics']['auto_repair_precision']:.3f}",
            "0.0%",
        ]]

        for name, dis in features[1:]:
            res = await BenchmarkExperimentService.run_experiment(
                method="PROPOSED_HYBRID",
                disabled_features=dis,
            )
            top1 = res["retrieval_metrics"]["top1_accuracy"]
            diff = (top1 - base_top1) * 100
            abl_rows.append([
                name,
                f"{top1:.3f}",
                f"{res['retrieval_metrics']['top3_accuracy']:.3f}",
                f"{res['retrieval_metrics']['mrr']:.3f}",
                f"{res['remediation_metrics']['auto_repair_precision']:.3f}",
                f"{diff:+.1f}%",
            ])

        print(format_table(abl_rows, abl_headers))

    else:
        method_map = {
            "baseline_url": "BASELINE_URL",
            "baseline_lexical": "BASELINE_LEXICAL",
            "semantic_only": "SEMANTIC_ONLY",
            "proposed_hybrid": "PROPOSED_HYBRID",
        }
        method = method_map.get(args.mode, "PROPOSED_HYBRID")
        print(f"\nExecuting single experiment: {method}...")
        res = await BenchmarkExperimentService.run_experiment(method=method)
        print(f"Top-1 Accuracy: {res['retrieval_metrics']['top1_accuracy']}")
        print(f"Top-3 Accuracy: {res['retrieval_metrics']['top3_accuracy']}")
        print(f"MRR:            {res['retrieval_metrics']['mrr']}")
        print(f"Repair Prec:    {res['remediation_metrics']['auto_repair_precision']}")

    print("\nBenchmark experiment execution complete.\n")


if __name__ == "__main__":
    asyncio.run(main())
