"""fpocket wrapper — geometric (Voronoi alpha-sphere) pocket detection.

fpocket вызывается как `fpocket -f input.pdb` и пишет вывод **рядом со входом**
в `{basename}_out/`:
    - `{basename}_info.txt` — Pocket Score, Druggability, и т.д. по каждому карману
    - `pockets/pocket{N}_atm.pdb` — атомы стенок кармана N

Поэтому копируем clean.pdb в `work_dir/fpocket/input.pdb` и работаем там
(иначе fpocket плодит мусор в корне job-кеша).

Score, который мы кладём в Pocket.score, — это `Pocket Score` из info.txt
(именно по нему fpocket ранжирует). Druggability сохраняем в radius'е?
Нет: druggability ≠ радиус. Радиус считаем геометрически — max(distance(centroid, atom)).
Druggability игнорируем для MVP (можно вернуть в schema на дне 6, если понадобится).
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from ..models.pocket import Method, MethodResult, Pocket


_POCKET_HEADER_RE = re.compile(r"^Pocket\s+(\d+)\s*:")
_SCORE_RE = re.compile(r"^\s*Score\s*:\s*([\-0-9.eE]+)")


def _resolve_fpocket() -> str:
    env_bin = os.environ.get("FPOCKET_BIN")
    if env_bin and Path(env_bin).is_file():
        return env_bin
    found = shutil.which("fpocket")
    if found:
        return found
    raise FileNotFoundError(
        "fpocket binary not found. Install in conda env: "
        "conda install -n annc -c conda-forge -c bioconda fpocket -y"
    )


def parse_info_txt(info_path: Path) -> dict[int, float]:
    """Прочитать `*_info.txt` и вернуть dict {pocket_rank: score}.

    Формат блока (отступы — табы):
        Pocket 1 :
        \tScore : \t0.701
        \tDruggability Score : \t0.532
        ...
    """
    scores: dict[int, float] = {}
    current: Optional[int] = None

    for raw_line in info_path.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            current = None
            continue
        m = _POCKET_HEADER_RE.match(line)
        if m:
            current = int(m.group(1))
            continue
        if current is not None and current not in scores:
            sm = _SCORE_RE.match(raw_line)
            if sm:
                scores[current] = float(sm.group(1))
    return scores


def parse_pocket_atm(pdb_path: Path) -> tuple[tuple[float, float, float], list[str], float]:
    """Извлечь из pocket{N}_atm.pdb:
       - centroid (mean of ATOM xyz)
       - unique residue ids в формате 'CHAIN_RESNUM' (стабильный порядок появления)
       - radius (max distance from centroid to any pocket atom)

    Raises ValueError если в файле нет ATOM-записей.
    """
    coords: list[tuple[float, float, float]] = []
    seen_residues: dict[str, None] = {}

    for line in pdb_path.read_text().splitlines():
        if not line.startswith(("ATOM", "HETATM")):
            continue
        try:
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])
        except ValueError:
            continue
        coords.append((x, y, z))
        chain = line[21].strip() or "_"
        resnum = line[22:26].strip()
        if resnum:
            seen_residues.setdefault(f"{chain}_{resnum}", None)

    if not coords:
        raise ValueError(f"no ATOM records in {pdb_path}")

    n = len(coords)
    cx = sum(c[0] for c in coords) / n
    cy = sum(c[1] for c in coords) / n
    cz = sum(c[2] for c in coords) / n

    radius = max(
        math.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
        for x, y, z in coords
    )

    return (cx, cy, cz), list(seen_residues), radius


def run_fpocket(pdb_path: Path, work_dir: Path, timeout_sec: int = 180) -> MethodResult:
    """Запустить fpocket и вернуть унифицированный результат.

    work_dir — корень кеша задачи; запуск идёт в work_dir/fpocket/.
    """
    fp_dir = work_dir / "fpocket"
    if fp_dir.exists():
        shutil.rmtree(fp_dir)
    fp_dir.mkdir(parents=True, exist_ok=True)

    input_pdb = fp_dir / "input.pdb"
    shutil.copy(pdb_path, input_pdb)

    try:
        fpocket_bin = _resolve_fpocket()
    except FileNotFoundError as exc:
        return MethodResult(method=Method.fpocket, error=str(exc))

    cmd = [fpocket_bin, "-f", input_pdb.name]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
            cwd=str(fp_dir),
        )
    except subprocess.TimeoutExpired:
        return MethodResult(
            method=Method.fpocket,
            error=f"fpocket timed out after {timeout_sec}s",
        )

    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-400:]
        return MethodResult(
            method=Method.fpocket,
            error=f"fpocket exit {proc.returncode}: {tail.strip()}",
        )

    out_dir = fp_dir / "input_out"
    info_path = out_dir / "input_info.txt"
    pockets_dir = out_dir / "pockets"
    if not info_path.is_file() or not pockets_dir.is_dir():
        return MethodResult(
            method=Method.fpocket,
            error=f"fpocket layout missing: {out_dir}",
        )

    scores = parse_info_txt(info_path)
    pockets: list[Pocket] = []
    for rank in sorted(scores.keys()):
        atm_path = pockets_dir / f"pocket{rank}_atm.pdb"
        if not atm_path.is_file():
            continue
        try:
            center, residues, radius = parse_pocket_atm(atm_path)
        except ValueError:
            continue
        pockets.append(
            Pocket(
                rank=rank,
                score=scores[rank],
                center=center,
                residues=residues,
                radius=round(radius, 2),
            )
        )

    if not pockets:
        return MethodResult(
            method=Method.fpocket,
            error="fpocket finished but no parseable pockets",
        )

    return MethodResult(method=Method.fpocket, pockets=pockets)
