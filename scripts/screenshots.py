"""Capture screenshots of the live UI for Pre-defense slides.

Запуск (предполагается uvicorn на :8000):
    source /home/ahamany/miniconda3/etc/profile.d/conda.sh && conda activate annc
    python scripts/screenshots.py

Кладёт PNG в docs/screenshots/:
    01_full_ui.png        — целиком главная страница после 1FBL done
    02_viewer.png         — только 3Dmol viewer
    03_comparison.png     — comparison + metrics плашки
    04_results_table.png  — таблица карманов
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8000"
PDB_ID = "1FBL"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        page.goto(BASE_URL, wait_until="networkidle")

        page.fill("#pdb-id", PDB_ID)
        page.click("#submit-btn")

        page.wait_for_function(
            "() => document.getElementById('status')?.textContent?.toLowerCase().includes('done')",
            timeout=60_000,
        )
        page.wait_for_timeout(2000)  # 3Dmol rendering settle

        page.screenshot(path=str(OUT / "01_full_ui.png"), full_page=True)
        print(f"  → {OUT / '01_full_ui.png'}")

        page.locator("#viewer").screenshot(path=str(OUT / "02_viewer.png"))
        print(f"  → {OUT / '02_viewer.png'}")

        # Comparison + metrics плашка + cross-method таблица (первые блоки .results-pane)
        page.evaluate(
            "() => { const t = document.getElementById('results-table'); if (t) t.style.display = 'none'; "
            "const h = document.querySelectorAll('.results-pane h2')[1]; if (h) h.style.display = 'none'; "
            "const b = document.getElementById('download-csv'); if (b) b.style.display = 'none'; }"
        )
        page.locator(".results-pane").screenshot(path=str(OUT / "03_comparison.png"))
        print(f"  → {OUT / '03_comparison.png'}")

        # Возвращаем как было, чтобы скриншот таблицы тоже был
        page.evaluate(
            "() => { const t = document.getElementById('results-table'); if (t) t.style.display = ''; "
            "const h = document.querySelectorAll('.results-pane h2')[1]; if (h) h.style.display = ''; "
            "const b = document.getElementById('download-csv'); if (b) b.style.display = ''; "
            "const cs = document.getElementById('comparison-summary'); if (cs) cs.style.display = 'none'; "
            "const ms = document.getElementById('metrics-summary'); if (ms) ms.style.display = 'none'; "
            "const ct = document.getElementById('comparison-table'); if (ct) ct.style.display = 'none'; "
            "const h0 = document.querySelectorAll('.results-pane h2')[0]; if (h0) h0.style.display = 'none'; }"
        )
        page.locator(".results-pane").screenshot(path=str(OUT / "04_results_table.png"))
        print(f"  → {OUT / '04_results_table.png'}")

        browser.close()


if __name__ == "__main__":
    main()
