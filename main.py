from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import re
from datetime import datetime

app = FastAPI(title="Helix Debugger")

# ========================
# Core Analyzer (unchanged)
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

    def analyze(self, log_text: str, recent_commits: Optional[List[str]] = None):
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

# ========================
# Beautiful Professional UI
# ========================

@app.get("/", response_class=HTMLResponse)
async def home():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Helix Debugger | AI-Powered Game Server Debugging</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap');
            body { font-family: 'Inter', system-ui; }
            .hero { background: linear-gradient(135deg, #0f172a, #1e2937); }
            .helical { animation: spin 25s linear infinite; }
        </style>
    </head>
    <body class="bg-zinc-950 text-zinc-200">
        <div class="max-w-7xl mx-auto">
            <!-- Hero -->
            <div class="hero py-24 px-8 text-center">
                <h1 class="text-6xl font-bold tracking-tighter text-white mb-4">Helix Debugger</h1>
                <p class="text-2xl text-cyan-400 mb-8">Instant root cause analysis for game servers</p>
                <p class="max-w-xl mx-auto text-lg text-zinc-400 mb-10">Drop your logs. Get ranked causes, reproduction steps, and clear explanations in seconds.</p>
                <a href="#analyze" class="inline-block bg-cyan-400 hover:bg-cyan-300 text-black font-semibold px-10 py-4 rounded-2xl text-xl transition">Try it Free Now</a>
            </div>

            <!-- How it Works -->
            <div class="py-16 px-8 bg-zinc-900">
                <h2 class="text-3xl font-semibold text-center mb-12">How Helix Debugger Works</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                    <div class="text-center">
                        <div class="w-12 h-12 mx-auto bg-cyan-400 text-black rounded-2xl flex items-center justify-center text-2xl font-bold mb-4">1</div>
                        <h3 class="text-xl font-medium mb-2">Upload Your Log</h3>
                        <p class="text-zinc-400">Drag & drop or paste server logs, crash dumps, or performance data.</p>
                    </div>
                    <div class="text-center">
                        <div class="w-12 h-12 mx-auto bg-cyan-400 text-black rounded-2xl flex items-center justify-center text-2xl font-bold mb-4">2</div>
                        <h3 class="text-xl font-medium mb-2">Instant Analysis</h3>
                        <p class="text-zinc-400">AI instantly ranks root causes with confidence scores and reproduction steps.</p>
                    </div>
                    <div class="text-center">
                        <div class="w-12 h-12 mx-auto bg-cyan-400 text-black rounded-2xl flex items-center justify-center text-2xl font-bold mb-4">3</div>
                        <h3 class="text-xl font-medium mb-2">Fix & Ship</h3>
                        <p class="text-zinc-400">Clear next actions. Fix faster. Ship your game.</p>
                    </div>
                </div>
            </div>

            <!-- Pricing -->
            <div id="analyze" class="py-16 px-8 bg-zinc-950">
                <h2 class="text-3xl font-semibold text-center mb-4">Simple Pricing</h2>
                <p class="text-center text-zinc-400 mb-12">Start free. Scale when you're ready.</p>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                    <!-- Free -->
                    <div class="border border-zinc-700 rounded-3xl p-8 text-center">
                        <h3 class="text-2xl font-semibold mb-2">Free</h3>
                        <p class="text-4xl font-bold mb-6">$0<span class="text-sm font-normal text-zinc-400">/month</span></p>
                        <ul class="space-y-3 text-left mb-8">
                            <li>15 analyses per month</li>
                            <li>Basic reports</li>
                            <li>Community support</li>
                        </ul>
                        <a href="#" class="block w-full py-4 bg-zinc-800 hover:bg-zinc-700 rounded-2xl font-medium">Get Started Free</a>
                    </div>
                    <!-- Pro -->
                    <div class="border border-cyan-400 rounded-3xl p-8 text-center scale-105 shadow-2xl">
                        <div class="text-cyan-400 text-sm font-semibold mb-1">MOST POPULAR</div>
                        <h3 class="text-2xl font-semibold mb-2">Pro</h3>
                        <p class="text-4xl font-bold mb-6">$49<span class="text-sm font-normal text-zinc-400">/month</span></p>
                        <ul class="space-y-3 text-left mb-8">
                            <li>Unlimited analyses</li>
                            <li>Full history &amp; exports</li>
                            <li>Team of up to 5</li>
                            <li>Priority support</li>
                        </ul>
                        <a href="#" onclick="alert('Stripe Checkout coming soon - contact us for early access')" class="block w-full py-4 bg-cyan-400 hover:bg-cyan-300 text-black rounded-2xl font-semibold">Upgrade to Pro</a>
                    </div>
                    <!-- Studio -->
                    <div class="border border-zinc-700 rounded-3xl p-8 text-center">
                        <h3 class="text-2xl font-semibold mb-2">Studio</h3>
                        <p class="text-4xl font-bold mb-6">$199<span class="text-sm font-normal text-zinc-400">/month</span></p>
                        <ul class="space-y-3 text-left mb-8">
                            <li>Everything in Pro</li>
                            <li>Priority AI processing</li>
                            <li>Custom integrations</li>
                            <li>Dedicated support</li>
                        </ul>
                        <a href="#" onclick="alert('Stripe Checkout coming soon - contact us for early access')" class="block w-full py-4 bg-zinc-800 hover:bg-zinc-700 rounded-2xl font-medium">Upgrade to Studio</a>
                    </div>
                </div>
            </div>

            <div class="text-center py-12 text-zinc-400 text-sm">
                Helix Debugger • Built to help game developers ship faster
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
