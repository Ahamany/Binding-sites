"""Apo/holo case study (e.g., HSP90: 1YES apo vs 1YET holo).

Логика:
    1. Прогон обеих структур через общий pipeline (preprocess → P2Rank + fpocket).
    2. ligand_center — ТОЛЬКО из holo (apo по определению без лиганда).
    3. DCC top-1/top-3 + success считаются для ОБЕИХ структур относительно
       holo-ligand-center: apo «успешен», если метод нашёл карман рядом с тем
       местом, где лиганд сядет в holo-форме (cryptic site detection).
    4. Дополнительно — расстояние между top-1 карманами apo и holo
       (диагностика: метод выдаёт «тот же» карман или совершенно другой).

Запуск:
    python -m benchmark.apo_holo --apo 1YES --holo 1YET \\
        --out benchmark/apo_holo_report.md
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.eval.dcc import evaluate_metrics, extract_ligand_center  # noqa: E402
from app.models.pocket import MethodResult, Metrics, Pocket  # noqa: E402
from app.services.binding_site import PDBNotFoundError, fetch_pdb  # noqa: E402
from app.tools.fpocket import run_fpocket  # noqa: E402
from app.tools.p2rank import run_p2rank  # noqa: E402
from app.tools.preprocess import preprocess_pdb  # noqa: E402


SUCCESS_THRESHOLD_A = 4.0


@dataclass
class StructureRun:
    pdb_id: str
    error: Optional[str] = None
    results: dict[str, MethodResult] = field(default_factory=dict)
    metrics: dict[str, Metrics] = field(default_factory=dict)
    runtime_sec: float = 0.0

    def top1(self, method: str) -> Optional[Pocket]:
        res = self.results.get(method)
        if res is None or not res.pockets:
            return None
        return min(res.pockets, key=lambda p: p.rank)


def _euclidean(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def _run_pipeline(pdb_id: str, work_root: Path) -> tuple[StructureRun, Path]:
    """Запустить полный pipeline один раз. Метрики не считаются."""
    rep = StructureRun(pdb_id=pdb_id)
    t0 = time.time()
    work_dir = work_root / pdb_id.upper()
    work_dir.mkdir(parents=True, exist_ok=True)
    input_pdb = work_dir / "input.pdb"
    try:
        if not input_pdb.exists():
            fetch_pdb(pdb_id, input_pdb)
        clean_pdb = work_dir / "clean.pdb"
        preprocess_pdb(input_pdb, clean_pdb)
        with ThreadPoolExecutor(max_workers=2) as ex:
            p2 = ex.submit(run_p2rank, clean_pdb, work_dir).result()
            fp = ex.submit(run_fpocket, clean_pdb, work_dir).result()
        rep.results = {"p2rank": p2, "fpocket": fp}
    except PDBNotFoundError as e:
        rep.error = f"fetch failed: {e}"
    except ValueError as e:
        rep.error = f"preprocess failed: {e}"
    except Exception as e:  # noqa: BLE001
        rep.error = f"{type(e).__name__}: {e}"
    rep.runtime_sec = round(time.time() - t0, 1)
    return rep, input_pdb


def _fill_metrics(rep: StructureRun, ligand_center: tuple[float, float, float]) -> None:
    for name, res in rep.results.items():
        if not res.error:
            rep.metrics[name] = evaluate_metrics(res, ligand_center)


def _cell_pocket(p: Optional[Pocket]) -> str:
    if p is None:
        return "—"
    cx, cy, cz = p.center
    return f"({cx:.1f}, {cy:.1f}, {cz:.1f})"


def _cell_dcc(m: Optional[Metrics]) -> str:
    if m is None or m.dcc_top1 is None:
        return "—"
    mark = "✓" if m.success_top3 else "✗"
    return f"top-1 = {m.dcc_top1:.2f} Å {mark}"


def _verdict(success: Optional[bool]) -> str:
    if success is None:
        return "—"
    return "✓ cryptic site found" if success else "✗ wrong pocket"


def _interpret(apo: StructureRun, holo: StructureRun) -> list[str]:
    out: list[str] = []
    for method in ("p2rank", "fpocket"):
        apo_m = apo.metrics.get(method)
        holo_m = holo.metrics.get(method)
        apo_p = apo.top1(method)
        holo_p = holo.top1(method)
        if apo_m is None or holo_m is None or apo_p is None or holo_p is None:
            out.append(f"- **{method}** — недостаточно данных (один из прогонов не вернул top-1).")
            continue
        delta = _euclidean(apo_p.center, holo_p.center)
        out.append(
            f"- **{method}** — top-1 apo и top-1 holo разнесены на "
            f"**{delta:.2f} Å**. DCC top-1 apo = {apo_m.dcc_top1:.2f} Å, "
            f"holo = {holo_m.dcc_top1:.2f} Å. Apo verdict: **{_verdict(apo_m.success_top3)}**."
        )
    return out


def write_report(out: Path, apo: StructureRun, holo: StructureRun) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Apo/holo case study — {apo.pdb_id} (apo) vs {holo.pdb_id} (holo)",
        "",
        "Reference binding-site — центр co-crystallized лиганда из **holo**.",
        f"Threshold success: DCC ≤ {SUCCESS_THRESHOLD_A} Å.",
        "",
        "## Per-structure summary",
        "",
        "| Structure | Method | Top-1 center (Å) | DCC | Runtime |",
        "|---|---|---|---|---|",
    ]
    for label, rep in (("apo", apo), ("holo", holo)):
        rt = f"{rep.runtime_sec}s"
        for method in ("p2rank", "fpocket"):
            lines.append(
                f"| {label} ({rep.pdb_id}) | {method} | "
                f"{_cell_pocket(rep.top1(method))} | "
                f"{_cell_dcc(rep.metrics.get(method))} | {rt} |"
            )

    lines += ["", "## Cross-form interpretation", ""]
    lines += _interpret(apo, holo)

    notes = []
    if apo.error:
        notes.append(f"- apo ({apo.pdb_id}) error: {apo.error}")
    if holo.error:
        notes.append(f"- holo ({holo.pdb_id}) error: {holo.error}")
    if notes:
        lines += ["", "## Notes", ""] + notes

    out.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apo/holo binding-site case study")
    parser.add_argument("--apo", required=True, help="PDB ID для apo-формы")
    parser.add_argument("--holo", required=True, help="PDB ID для holo-формы")
    parser.add_argument(
        "--out", type=Path,
        default=PROJECT_ROOT / "benchmark" / "apo_holo_report.md",
    )
    parser.add_argument(
        "--work", type=Path,
        default=PROJECT_ROOT / "benchmark" / "work",
    )
    parser.add_argument(
        "--ligand", default=None,
        help="Override ligand resname в holo (по умолчанию — auto-detect)",
    )
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)

    print(f"[apo_holo] running apo {args.apo}…", flush=True)
    apo_run, _ = _run_pipeline(args.apo, args.work)
    print(f"  → {apo_run.runtime_sec}s" + (f" SKIP: {apo_run.error}" if apo_run.error else ""))

    print(f"[apo_holo] running holo {args.holo}…", flush=True)
    holo_run, holo_input = _run_pipeline(args.holo, args.work)
    print(f"  → {holo_run.runtime_sec}s" + (f" SKIP: {holo_run.error}" if holo_run.error else ""))

    ligand_center: Optional[tuple[float, float, float]] = None
    if not holo_run.error:
        ligand_center = extract_ligand_center(holo_input, resname_override=args.ligand)

    if ligand_center is None:
        print(f"[apo_holo] WARN: no co-crystallized ligand in holo {args.holo}; metrics will be empty.")
    else:
        _fill_metrics(apo_run, ligand_center)
        _fill_metrics(holo_run, ligand_center)

    write_report(args.out, apo_run, holo_run)
    print(f"\n[apo_holo] Report → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
