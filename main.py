from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
import re
from datetime import datetime
import uuid

app = FastAPI(title="Helix Debugger")

# ========================
# Core Analyzer
# ========================

class HelixDebugger:
    def __init__(self):
        self.patterns = {
            "memory_leak": re.compile(r"(memory.*leak|alloc.*fail|heap.*corrupt|OutOfMemory)", re.IGNORECASE),
            "desync": re.compile(r"(desync|state mismatch|packet loss|replication error)", re.IGNORECASE),
            "crash": re.compile(r"(Exception|Assertion failed|Segmentation fault|NullReference)", re.IGNORECASE),
            "race_condition": re.compile(r"(race|thread|concurrent|deadlock)", re.IGNORECASE),
            "network_spike": re.compile(r"(latency|timeout|packet.*drop)", re.IGNORECASE),
        }

    def analyze(self, log_text: str, recent_commits: Optional[List[str]] = None) -> Dict:
        results = []
        for bug_type, pattern in self.patterns.items():
            matches = pattern.findall(log_text)
            if matches:
                results.append({
                    "type": bug_type.replace("_", " ").title(),
                    "confidence": min(len(matches) * 25, 95),
                    "matches": matches[:5]
                })

        summary = self._generate_summary(log_text, results, recent_commits)
        reproduction = self._generate_reproduction_steps(results)

        return {
            "summary": summary,
            "ranked_causes": sorted(results, key=lambda x: x["confidence"], reverse=True),
            "reproduction_suggestions": reproduction
        }

    def _generate_summary(self, log_text: str, results: List[dict], recent_commits: Optional[List[str]]) -> str:
        if not results:
            return "No clear patterns detected. Check for subtle timing or environment-specific issues."
        
        top = results[0]
        text = f"Most likely root cause: **{top['type']}** ({top['confidence']}% confidence)\n\nKey evidence:\n"
        for r in results[:3]:
            text += f"• {r['type']}: {len(r['matches'])} matches\n"
        
        if recent_commits:
            text += "\nRecent changes that may be related:\n"
            for c in recent_commits[:3]:
                text += f"  • {c}\n"
        return text.strip()

    def _generate_reproduction_steps(self, results: List[dict]) -> List[str]:
        steps = []
        top_type = results[0]["type"].lower() if results else ""
        if "crash" in top_type:
            steps = ["Reproduce with exact player count and actions", "Check stack trace line numbers", "Test with same game state"]
        elif "desync" in top_type:
            steps = ["Test with 50+ players in same area", "Simulate high latency", "Compare server and client state"]
        elif "memory_leak" in top_type:
            steps = ["Run long stress test (30+ minutes)", "Monitor memory usage over time", "Look for repeated spawning actions"]
        else:
            steps = ["Reproduce exact conditions in the log", "Check recent code changes", "Test in clean environment"]
        return steps


debugger = HelixDebugger()

# Simple in-memory storage for demo (history & projects)
history = {}

class AnalysisRequest(BaseModel):
    log_text: str
    recent_commits: Optional[List[str]] = None
    project_id: Optional[str] = None

@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    result = debugger.analyze(request.log_text, request.recent_commits)
    analysis_id = str(uuid.uuid4())
    history[analysis_id] = result
    return {"analysis_id": analysis_id, **result}

@app.get("/history")
async def get_history():
    return {"history": history}

@app.get("/", response_class=HTMLResponse)
async def home():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Helix Debugger</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
            body { font-family: 'Inter', system-ui; background: #0a0a0f; color: #e0e0e0; }
            .hero-bg { background: linear-gradient(135deg, #111827, #1e2937); }
            .helical { animation: helical-spin 20s linear infinite; }
        </style>
    </head>
    <body class="min-h-screen">
        <div class="max-w-7xl mx-auto px-6 py-12">
            <div class="flex justify-between items-center mb-12">
                <h1 class="text-4xl font-semibold tracking-tight text-cyan-400">Helix Debugger</h1>
                <div class="text-sm text-gray-400">High-Tech Debugging for Game Developers</div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">
                <!-- Left: Upload & Analysis -->
                <div class="bg-zinc-900 rounded-3xl p-8 border border-cyan-500/20">
                    <h2 class="text-2xl font-medium mb-6">Analyze Your Log</h2>
                    <div id="dropzone" class="border-2 border-dashed border-cyan-400/60 rounded-2xl p-12 text-center hover:border-cyan-400 transition-colors cursor-pointer">
                        <p class="text-cyan-300">Drop log file here or click to upload</p>
                    </div>
                    <textarea id="logtext" rows="6" class="w-full mt-6 bg-zinc-800 text-white rounded-2xl p-6 focus:outline-none focus:ring-2 focus:ring-cyan-400" placeholder="Or paste your log here..."></textarea>
                    <button onclick="analyzeLog()" class="mt-6 w-full bg-gradient-to-r from-cyan-400 to-blue-500 text-black font-semibold py-4 rounded-2xl text-lg hover:scale-105 transition-transform">Analyze Now</button>
                </div>

                <!-- Right: Results & History -->
                <div class="bg-zinc-900 rounded-3xl p-8 border border-cyan-500/20">
                    <h2 class="text-2xl font-medium mb-6">Analysis Results</h2>
                    <div id="results" class="min-h-[400px] text-sm"></div>
                </div>
            </div>
        </div>

        <script>
            async function analyzeLog() {
                const text = document.getElementById('logtext').value;
                const res = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({log_text: text})
                });
                const data = await res.json();
                document.getElementById('results').innerHTML = `
                    <div class="text-cyan-300 font-medium">${data.summary}</div>
                    <div class="mt-6">
                        <h3 class="text-lg mb-3">Ranked Causes</h3>
                        ${data.ranked_causes.map(c => `<div class="bg-zinc-800 rounded-xl p-4 mb-3"><strong>${c.type}</strong> <span class="text-cyan-400">(${c.confidence}%)</span></div>`).join('')}
                    </div>
                `;
            }

            // Basic drag & drop support
            const dropzone = document.getElementById('dropzone');
            dropzone.addEventListener('click', () => document.getElementById('logtext').focus());
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
