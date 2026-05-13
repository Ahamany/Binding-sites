// Frontend: upload PDB → poll for results → render in 3Dmol.js.

const API_BASE = "/api";
const POLL_INTERVAL_MS = 1500;
const LARGE_ATOM_THRESHOLD = 8000;   // Risk R3: warn пользователя что вьюер может тормозить

const METHOD_COLORS = {
    p2rank: "#4ea1f3",
    fpocket: "#f08c4e",
};

const $ = (sel) => document.querySelector(sel);

let viewer = null;
let viewerModel = null;
let currentJobId = null;
let currentJobResult = null;          // последний JobResult с бэка
let pocketShapes = { p2rank: [], fpocket: [] };
let highlightShapeId = null;          // временная сфера для hover-подсветки

function ensureViewer() {
    if (viewer) return viewer;
    viewer = $3Dmol.createViewer("viewer", { backgroundColor: 0x0f1419 });
    return viewer;
}

function setStatus(text, kind = "") {
    const el = $("#status");
    el.textContent = text;
    el.className = "status " + kind;
}

async function createJob(formData) {
    const res = await fetch(`${API_BASE}/jobs`, { method: "POST", body: formData });
    if (!res.ok) {
        throw new Error(`POST /jobs failed: ${res.status} ${await res.text()}`);
    }
    return res.json();
}

async function pollJob(jobId) {
    while (true) {
        const res = await fetch(`${API_BASE}/jobs/${jobId}`);
        if (!res.ok) throw new Error(`GET /jobs/${jobId} failed: ${res.status}`);
        const job = await res.json();
        setStatus(`status: ${job.status}`, job.status);
        if (job.status === "done" || job.status === "failed") return job;
        await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
    }
}

async function loadStructure(jobId) {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/structure`);
    if (!res.ok) throw new Error(`GET /jobs/${jobId}/structure failed: ${res.status}`);
    const pdbText = await res.text();
    const v = ensureViewer();
    v.removeAllModels();
    v.removeAllShapes();
    highlightShapeId = null;
    viewerModel = v.addModel(pdbText, "pdb");
    v.setStyle({}, { cartoon: { color: "spectrum" } });
    v.zoomTo();
    v.render();

    const atomCount = viewerModel.selectedAtoms({}).length;
    if (atomCount > LARGE_ATOM_THRESHOLD) {
        setStatus(`done (large structure: ${atomCount} atoms, viewer may be slow)`, "warning");
    }
}

function clearPocketShapes() {
    const v = ensureViewer();
    v.removeAllShapes();
    pocketShapes = { p2rank: [], fpocket: [] };
}

function drawPocketsForMethod(method) {
    const v = ensureViewer();
    if (!currentJobResult) return;
    const methodResult = currentJobResult.results?.[method];
    if (!methodResult) return;

    for (const pocket of methodResult.pockets) {
        const sphere = v.addSphere({
            center: { x: pocket.center[0], y: pocket.center[1], z: pocket.center[2] },
            radius: pocket.radius || 4.0,
            color: METHOD_COLORS[method],
            opacity: 0.55,
        });
        pocketShapes[method].push(sphere);
    }
    v.render();
}

function refreshViewerOverlays() {
    clearPocketShapes();
    highlightShapeId = null;
    document.querySelectorAll('.method-toggles input[type="checkbox"]').forEach((cb) => {
        if (cb.checked) drawPocketsForMethod(cb.dataset.method);
    });
}

function highlightPocket(method, rank) {
    const v = ensureViewer();
    if (highlightShapeId !== null) {
        v.removeShape(highlightShapeId);
        highlightShapeId = null;
    }
    if (method === null || rank === null) {
        v.render();
        return;
    }
    if (!currentJobResult) return;
    const pocket = currentJobResult.results?.[method]?.pockets?.find(p => p.rank === rank);
    if (!pocket) return;
    highlightShapeId = v.addSphere({
        center: { x: pocket.center[0], y: pocket.center[1], z: pocket.center[2] },
        radius: (pocket.radius || 4.0) * 1.15,
        color: METHOD_COLORS[method],
        opacity: 0.9,
        wireframe: true,
    });
    v.render();
}

function zoomToPocket(method, rank) {
    if (!currentJobResult) return;
    const pocket = currentJobResult.results?.[method]?.pockets?.find(p => p.rank === rank);
    if (!pocket || !pocket.residues?.length) return;

    const chains = new Set();
    const resnums = [];
    for (const r of pocket.residues) {
        const [chain, resnum] = r.split("_");
        chains.add(chain);
        const n = Number(resnum);
        if (Number.isFinite(n)) resnums.push(n);
    }
    if (!resnums.length) return;

    const sel = chains.size === 1
        ? { chain: [...chains][0], resi: resnums }
        : { resi: resnums };
    ensureViewer().zoomTo(sel, 500);
}

function renderMetrics(job) {
    const el = $("#metrics-summary");
    const metrics = job.metrics || {};
    const parts = [];
    for (const method of ["p2rank", "fpocket"]) {
        const mm = metrics[method];
        if (!mm || mm.dcc_top1 == null) continue;
        const tag = `<span class="method-tag ${method}">${method}</span>`;
        const dcc = mm.dcc_top1.toFixed(2);
        const verdict = mm.success_top3
            ? '<span class="ok">✓</span>'
            : '<span class="fail">✗</span>';
        parts.push(`${tag} DCC top-1: <strong>${dcc} Å</strong> ${verdict}`);
    }
    if (!parts.length) {
        el.hidden = true;
        el.innerHTML = "";
        return;
    }
    el.innerHTML = parts.join(" · ");
    el.hidden = false;
}

function renderComparisonPanel(job) {
    const summary = $("#comparison-summary");
    const table = $("#comparison-table");
    const tbody = table.querySelector("tbody");
    tbody.innerHTML = "";

    const matches = job.comparison || [];
    if (matches.length === 0) {
        summary.textContent = "No comparison available (one of the methods returned no pockets).";
        table.hidden = true;
        return;
    }

    const top1 = matches.find(m => m.p2rank_rank === 1) || matches[0];
    summary.innerHTML =
        `P2Rank #${top1.p2rank_rank} ↔ fpocket #${top1.fpocket_rank}: ` +
        `<strong>${top1.distance.toFixed(2)} Å</strong> apart · ` +
        `Jaccard <strong>${top1.jaccard.toFixed(2)}</strong>`;

    for (const m of matches) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><span class="method-tag p2rank">#${m.p2rank_rank}</span></td>
            <td class="muted">↔</td>
            <td><span class="method-tag fpocket">#${m.fpocket_rank}</span></td>
            <td>${m.distance.toFixed(2)}</td>
            <td>${m.jaccard.toFixed(2)}</td>`;
        tbody.appendChild(tr);
    }
    table.hidden = false;
}

async function downloadCsv() {
    if (!currentJobId) return;
    try {
        const res = await fetch(`${API_BASE}/jobs/${currentJobId}/results.csv`);
        if (!res.ok) throw new Error(`CSV download failed: ${res.status}`);
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${currentJobId}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (err) {
        setStatus(err.message, "failed");
    }
}

function renderResultsTable(job) {
    const tbody = $("#results-table tbody");
    tbody.innerHTML = "";

    let hasPockets = false;
    for (const [method, mr] of Object.entries(job.results || {})) {
        if (mr.error) {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><span class="method-tag ${method}">${method}</span></td>
                <td colspan="4"><em style="color:var(--muted)">${mr.error}</em></td>`;
            tbody.appendChild(tr);
            continue;
        }
        for (const p of mr.pockets) {
            hasPockets = true;
            const tr = document.createElement("tr");
            tr.dataset.method = method;
            tr.dataset.rank = String(p.rank);
            const center = p.center.map((v) => v.toFixed(1)).join(", ");
            const residues = (p.residues || []).slice(0, 8).join(", ") + (p.residues.length > 8 ? "…" : "");
            tr.innerHTML = `
                <td><span class="method-tag ${method}">${method}</span></td>
                <td>${p.rank}</td>
                <td>${p.score.toFixed(2)}</td>
                <td>${center}</td>
                <td>${residues}</td>`;
            tr.addEventListener("mouseenter", () => highlightPocket(method, p.rank));
            tr.addEventListener("mouseleave", () => highlightPocket(null, null));
            tr.addEventListener("click", () => zoomToPocket(method, p.rank));
            tbody.appendChild(tr);
        }
    }
    $("#download-csv").hidden = !hasPockets;
}

$("#job-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const pdbId = $("#pdb-id").value.trim();
    const file = $("#pdb-file").files[0];
    if (!pdbId && !file) {
        setStatus("Provide PDB ID or upload a file", "failed");
        return;
    }

    const fd = new FormData();
    if (pdbId) fd.append("pdb_id", pdbId);
    if (file)  fd.append("file", file);

    $("#submit-btn").disabled = true;
    $("#download-csv").hidden = true;
    $("#metrics-summary").hidden = true;
    try {
        setStatus("creating job…", "queued");
        const { job_id } = await createJob(fd);
        currentJobId = job_id;
        const job = await pollJob(job_id);

        if (job.status === "failed") {
            setStatus(`failed: ${job.error}`, "failed");
            return;
        }

        await loadStructure(job_id);
        currentJobResult = job;
        $("#method-toggles").hidden = false;
        renderComparisonPanel(job);
        renderMetrics(job);
        renderResultsTable(job);
        refreshViewerOverlays();
    } catch (err) {
        setStatus(err.message, "failed");
    } finally {
        $("#submit-btn").disabled = false;
    }
});

document.querySelectorAll('.method-toggles input[type="checkbox"]').forEach((cb) => {
    cb.addEventListener("change", refreshViewerOverlays);
});

$("#download-csv").addEventListener("click", downloadCsv);

window.addEventListener("DOMContentLoaded", ensureViewer);
