"""P2Rank wrapper — surface-based ML detection of binding pockets.

P2Rank вызывается как `prank predict -f input.pdb -o out_dir`.
Результат — CSV `{out_dir}/{basename}_predictions.csv` с колонками:
    name, rank, score, probability, sas_points, surf_atoms,
    center_x, center_y, center_z, residue_ids, surf_atom_ids

Бинарь ищем в (приоритет ↓):
    1. env P2RANK_BIN
    2. third_party/p2rank/prank относительно корня проекта
    3. `prank` в PATH
"""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from ..models.pocket import Method, MethodResult, Pocket


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_P2RANK = PROJECT_ROOT / "third_party" / "p2rank" / "prank"


def _resolve_prank() -> str:
    env_bin = os.environ.get("P2RANK_BIN")
    if env_bin and Path(env_bin).is_file():
        return env_bin
    if DEFAULT_P2RANK.is_file():
        return str(DEFAULT_P2RANK)
    found = shutil.which("prank")
    if found:
        return found
    raise FileNotFoundError(
        "P2Rank binary not found. Set P2RANK_BIN, run scripts/install_p2rank.sh, "
        "or add prank to PATH."
    )


def parse_predictions_csv(csv_path: Path) -> list[Pocket]:
    """Распарсить *_predictions.csv от P2Rank в list[Pocket].

    Колонки P2Rank приходят с whitespace-padding (`'  rank'`),
    поэтому нормализуем заголовки и значения через strip().
    residue_ids — внутри одного CSV-поля, токены через пробел.
    """
    pockets: list[Pocket] = []
    with csv_path.open(newline="") as fh:
        reader = csv.reader(fh, skipinitialspace=True)
        try:
            header = [c.strip() for c in next(reader)]
        except StopIteration:
            return []
        idx = {name: i for i, name in enumerate(header)}
        required = ("rank", "score", "center_x", "center_y", "center_z")
        for col in required:
            if col not in idx:
                raise ValueError(f"P2Rank CSV missing column '{col}': header={header}")

        for row in reader:
            if not row or not row[0].strip():
                continue
            try:
                rank = int(row[idx["rank"]].strip())
                score = float(row[idx["score"]].strip())
                cx = float(row[idx["center_x"]].strip())
                cy = float(row[idx["center_y"]].strip())
                cz = float(row[idx["center_z"]].strip())
            except (ValueError, IndexError) as exc:
                raise ValueError(f"P2Rank CSV row parse error: {row!r}") from exc

            residues: list[str] = []
            if "residue_ids" in idx and idx["residue_ids"] < len(row):
                raw = row[idx["residue_ids"]].strip()
                if raw:
                    residues = raw.split()

            pockets.append(
                Pocket(
                    rank=rank,
                    score=score,
                    center=(cx, cy, cz),
                    residues=residues,
                    radius=None,
                )
            )

    pockets.sort(key=lambda p: p.rank)
    return pockets


def _find_predictions_csv(out_dir: Path) -> Optional[Path]:
    matches = sorted(out_dir.glob("*_predictions.csv"))
    return matches[0] if matches else None


def run_p2rank(pdb_path: Path, work_dir: Path, timeout_sec: int = 180) -> MethodResult:
    """Запустить P2Rank и вернуть унифицированный результат.

    work_dir — корень кеша задачи; вывод P2Rank пойдёт в work_dir/p2rank/.
    """
    out_dir = work_dir / "p2rank"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        prank = _resolve_prank()
    except FileNotFoundError as exc:
        return MethodResult(method=Method.p2rank, error=str(exc))

    cmd = [prank, "predict", "-f", str(pdb_path), "-o", str(out_dir)]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return MethodResult(
            method=Method.p2rank,
            error=f"P2Rank timed out after {timeout_sec}s",
        )

    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-400:]
        return MethodResult(
            method=Method.p2rank,
            error=f"P2Rank exit {proc.returncode}: {tail.strip()}",
        )

    csv_path = _find_predictions_csv(out_dir)
    if csv_path is None:
        return MethodResult(
            method=Method.p2rank,
            error=f"P2Rank produced no *_predictions.csv in {out_dir}",
        )

    try:
        pockets = parse_predictions_csv(csv_path)
    except ValueError as exc:
        return MethodResult(method=Method.p2rank, error=str(exc))

    return MethodResult(method=Method.p2rank, pockets=pockets)
