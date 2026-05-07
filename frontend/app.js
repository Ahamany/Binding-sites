// Frontend skeleton: upload PDB → poll for results → render in 3Dmol.js.
// Полная отрисовка карманов — день 5 (после P2Rank/fpocket wrappers).

const API_BASE = "/api";
const POLL_INTERVAL_MS = 1500;

const METHOD_COLORS = {
    p2rank: "#4ea1f3",
    fpocket: "#f08c4e",
};

const $ = (sel) => document.querySelector(sel);

let viewer = null;
let viewerModel = null;
let currentJobResult = null;          // последний JobResult с бэка
let pocketShapes = { p2rank: [], fpocket: [] };

function ensureViewer() {
    if (viewer) return viewer;
    viewer = $3Dmol.createViewer("viewer", { backgroundColor: "0x0f1419" });
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
    viewerModel = v.addModel(pdbText, "pdb");
    v.setStyle({}, { cartoon: { color: "spectrum" } });
    v.zoomTo();
    v.render();
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
    document.querySelectorAll('.method-toggles input[type="checkbox"]').forEach((cb) => {
        if (cb.checked) drawPocketsForMethod(cb.dataset.method);
    });
}

function renderResultsTable(job) {
    const tbody = $("#results-table tbody");
    tbody.innerHTML = "";

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
            const tr = document.createElement("tr");
            const center = p.center.map((v) => v.toFixed(1)).join(", ");
            const residues = (p.residues || []).slice(0, 8).join(", ") + (p.residues.length > 8 ? "…" : "");
            tr.innerHTML = `
                <td><span class="method-tag ${method}">${method}</span></td>
                <td>${p.rank}</td>
                <td>${p.score.toFixed(2)}</td>
                <td>${center}</td>
                <td>${residues}</td>`;
            tbody.appendChild(tr);
        }
    }
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
    try {
        setStatus("creating job…", "queued");
        const { job_id } = await createJob(fd);
        const job = await pollJob(job_id);

        await loadStructure(job_id);
        currentJobResult = job;
        $("#method-toggles").hidden = false;
        renderResultsTable(job);
        refreshViewerOverlays();

        if (job.status === "failed") {
            setStatus(`failed: ${job.error}`, "failed");
        }
    } catch (err) {
        setStatus(err.message, "failed");
    } finally {
        $("#submit-btn").disabled = false;
    }
});

document.querySelectorAll('.method-toggles input[type="checkbox"]').forEach((cb) => {
    cb.addEventListener("change", refreshViewerOverlays);
});

window.addEventListener("DOMContentLoaded", ensureViewer);
