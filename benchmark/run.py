"""COACH420 subset benchmark — прогон списка PDB через P2Rank + fpocket + DCC eval.

Запуск:
    python -m benchmark.run \\
        --subset benchmark/coach420_subset.csv \\
        --out benchmark/report.md \\
        --work benchmark/work

Логика per-PDB:
    fetch (если нет в work/) → extract_ligand_center → preprocess →
    run_p2rank ‖ run_fpocket (параллельно) → evaluate_metrics → строка отчёта.

Graceful skip: network fail / no ligand / tool error → строка с (skipped: ...).
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.eval.dcc import evaluate_metrics, extract_ligand_center  # noqa: E402
from app.models.pocket import MethodResult, Metrics  # noqa: E402
from app.services.binding_site import PDBNotFoundError, fetch_pdb  # noqa: E402
from app.tools.fpocket import run_fpocket  # noqa: E402
from app.tools.p2rank import run_p2rank  # noqa: E402
from app.tools.preprocess import preprocess_pdb  # noqa: E402


@dataclass
class PdbRow:
    pdb_id: str
    ligand_resname: Optional[str] = None


@dataclass
class PdbReport:
    pdb_id: str
    ligand_resname: Optional[str] = None
    error: Optional[str] = None
    metrics: dict[str, Metrics] = field(default_factory=dict)
    pocket_counts: dict[str, int] = field(default_factory=dict)
    runtime_sec: float = 0.0


def load_subset(path: Path) -> list[PdbRow]:
    rows: list[PdbRow] = []
    with path.open() as fh:
        for r in csv.DictReader(fh):
            pdb_id = (r.get("pdb_id") or "").strip()
            if not pdb_id:
                continue
            lig = (r.get("ligand_resname") or "").strip() or None
            rows.append(PdbRow(pdb_id=pdb_id, ligand_resname=lig))
    return rows


def _process_one(row: PdbRow, work_root: Path) -> PdbReport:
    rep = PdbReport(pdb_id=row.pdb_id, ligand_resname=row.ligand_resname)
    t0 = time.time()
    try:
        work_dir = work_root / row.pdb_id.upper()
        work_dir.mkdir(parents=True, exist_ok=True)
        input_pdb = work_dir / "input.pdb"
        if not input_pdb.exists():
            fetch_pdb(row.pdb_id, input_pdb)

        ligand_center = extract_ligand_center(
            input_pdb, resname_override=row.ligand_resname
        )
        if ligand_center is None:
            rep.error = "no co-crystallized ligand found"
            return rep

        clean_pdb = work_dir / "clean.pdb"
        preprocess_pdb(input_pdb, clean_pdb)

        with ThreadPoolExecutor(max_workers=2) as ex:
            p2rank_future = ex.submit(run_p2rank, clean_pdb, work_dir)
            fpocket_future = ex.submit(run_fpocket, clean_pdb, work_dir)
            p2rank_res: MethodResult = p2rank_future.result()
            fpocket_res: MethodResult = fpocket_future.result()

        for name, res in (("p2rank", p2rank_res), ("fpocket", fpocket_res)):
            rep.pocket_counts[name] = len(res.pockets)
            if not res.error:
                rep.metrics[name] = evaluate_metrics(res, ligand_center)
    except PDBNotFoundError as e:
        rep.error = f"fetch failed: {e}"
    except ValueError as e:
        rep.error = f"preprocess failed: {e}"
    except Exception as e:  # noqa: BLE001
        rep.error = f"{type(e).__name__}: {e}"
    finally:
        rep.runtime_sec = round(time.time() - t0, 1)
    return rep


def _cell(metric: Optional[float], success: Optional[bool]) -> str:
    if metric is None:
        return "—"
    mark = "✓" if success else "✗"
    return f"{metric:.2f} Å {mark}"


def _row_md(rep: PdbReport) -> str:
    p2 = rep.metrics.get("p2rank")
    fp = rep.metrics.get("fpocket")
    p2_top1 = _cell(p2.dcc_top1 if p2 else None, p2.success_top3 if p2 else None)
    p2_top3 = _cell(p2.dcc_top3 if p2 else None, p2.success_top3 if p2 else None)
    fp_top1 = _cell(fp.dcc_top1 if fp else None, fp.success_top3 if fp else None)
    fp_top3 = _cell(fp.dcc_top3 if fp else None, fp.success_top3 if fp else None)
    lig = rep.ligand_resname or "(auto)"
    note = rep.error or ""
    return (
        f"| {rep.pdb_id} | {lig} | {p2_top1} | {p2_top3} | "
        f"{fp_top1} | {fp_top3} | {rep.runtime_sec}s | {note} |"
    )


def _summary_md(reports: list[PdbReport]) -> str:
    success = {"p2rank": 0, "fpocket": 0}
    evaluated = {"p2rank": 0, "fpocket": 0}
    for r in reports:
        for m in ("p2rank", "fpocket"):
            if m in r.metrics:
                evaluated[m] += 1
                if r.metrics[m].success_top3:
                    success[m] += 1

    skipped = sum(1 for r in reports if r.error)
    n = len(reports)

    def pct(a: int, b: int) -> str:
        return f"{100 * a / b:.0f}%" if b else "—"

    return "\n".join([
        "",
        "## Aggregate",
        "",
        f"- Total PDBs in subset: **{n}**",
        f"- Skipped (fetch/no-ligand/tool fail): **{skipped}**",
        f"- Successfully evaluated by P2Rank: **{evaluated['p2rank']}** / {n}",
        f"- Successfully evaluated by fpocket: **{evaluated['fpocket']}** / {n}",
        "",
        f"### P2Rank top-3 success rate: **{success['p2rank']}/{evaluated['p2rank']} = {pct(success['p2rank'], evaluated['p2rank'])}**",
        f"### fpocket top-3 success rate: **{success['fpocket']}/{evaluated['fpocket']} = {pct(success['fpocket'], evaluated['fpocket'])}**",
        "",
        "Threshold: top-3 success = min(DCC по top-3 карманам) ≤ 4.0 Å.",
    ])


def write_report(out: Path, reports: list[PdbReport]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "# COACH420 subset benchmark",
        "",
        "Cross-method evaluation на 15 PDB с co-crystallized лигандами.",
        "Метрика — DCC (Distance to Center of Cocrystal), threshold 4.0 Å.",
        "",
        "| PDB | Ligand | P2Rank top-1 | P2Rank top-3 | fpocket top-1 | fpocket top-3 | Runtime | Notes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    rows = [_row_md(r) for r in reports]
    out.write_text("\n".join(header + rows) + "\n" + _summary_md(reports) + "\n")


def _stdout_line(i: int, n: int, rep: PdbReport) -> str:
    if rep.error:
        return f"[{i}/{n}] {rep.pdb_id}: SKIP — {rep.error} ({rep.runtime_sec}s)"
    parts = []
    for name in ("p2rank", "fpocket"):
        m = rep.metrics.get(name)
        if m is None or m.dcc_top1 is None:
            continue
        mark = "✓" if m.success_top3 else "✗"
        parts.append(f"{name} top-1={m.dcc_top1:.2f}Å {mark}")
    body = " · ".join(parts) if parts else "no metrics"
    return f"[{i}/{n}] {rep.pdb_id}: {body} ({rep.runtime_sec}s)"


def main() -> int:
    parser = argparse.ArgumentParser(description="COACH420 batch DCC benchmark")
    parser.add_argument(
        "--subset", type=Path,
        default=PROJECT_ROOT / "benchmark" / "coach420_subset.csv",
    )
    parser.add_argument(
        "--out", type=Path,
        default=PROJECT_ROOT / "benchmark" / "report.md",
    )
    parser.add_argument(
        "--work", type=Path,
        default=PROJECT_ROOT / "benchmark" / "work",
    )
    args = parser.parse_args()

    rows = load_subset(args.subset)
    print(f"[benchmark] {len(rows)} PDBs from {args.subset}")

    args.work.mkdir(parents=True, exist_ok=True)
    reports: list[PdbReport] = []
    for i, row in enumerate(rows, 1):
        rep = _process_one(row, args.work)
        reports.append(rep)
        print(_stdout_line(i, len(rows), rep))

    write_report(args.out, reports)
    print(f"\n[benchmark] Report → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
