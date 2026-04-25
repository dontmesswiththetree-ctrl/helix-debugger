from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime
import hashlib

app = FastAPI(title="Helix Debugger")

# ========================
# Simple Database (Persistent)
# ========================
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        name TEXT,
        trials_left INTEGER DEFAULT 12,
        subscription TEXT DEFAULT 'free',
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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

    def analyze(self, log_text: str):
        # Simple placeholder - replace with your full analyzer if desired
        return {
            "summary": "Analysis complete. Most likely root cause: Network spike (82% confidence)",
            "ranked_causes": [{"type": "Network Spike", "confidence": 82}]
        }

debugger = HelixDebugger()

# ========================
# Professional Dashboard UI
# ========================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(username: str = "Daphne"):
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard - Helix Debugger</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            body {{ font-family: 'Inter', system-ui; background: #0a0a0f; color: #e0e0e0; }}
        </style>
    </head>
    <body class="min-h-screen bg-zinc-950">
        <div class="max-w-7xl mx-auto px-8 py-12">
            <div class="flex justify-between items-center mb-12">
                <div>
                    <h1 class="text-5xl font-bold text-cyan-400">Welcome back, {username}.</h1>
                    <p class="text-zinc-400 mt-2">Your personal AI debugging assistant.</p>
                </div>
                <div class="text-right">
                    <div class="inline-flex items-center bg-zinc-900 px-6 py-3 rounded-2xl">
                        <span class="text-emerald-400 font-semibold">12 Trials Left</span>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Trial Counter Card -->
                <div class="bg-zinc-900 rounded-3xl p-8 border border-cyan-400/30">
                    <h3 class="text-cyan-400 font-medium mb-2">Free Trial</h3>
                    <div class="flex items-center justify-between">
                        <div class="text-7xl font-bold text-white">12</div>
                        <div class="text-right">
                            <div class="text-sm text-zinc-400">analyses remaining</div>
                            <div class="h-2 bg-zinc-800 rounded-full mt-3 w-32">
                                <div class="h-2 bg-cyan-400 rounded-full w-3/4"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Subscription Status -->
                <div class="bg-zinc-900 rounded-3xl p-8">
                    <h3 class="text-zinc-400 mb-2">Current Plan</h3>
                    <div class="flex items-center gap-3">
                        <span class="px-5 py-2 bg-emerald-400 text-black font-semibold rounded-2xl text-sm">FREE</span>
                        <span class="text-zinc-400">Next upgrade available</span>
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="bg-zinc-900 rounded-3xl p-8 flex flex-col gap-4">
                    <a href="#" class="flex-1 bg-cyan-400 hover:bg-cyan-300 text-black font-semibold py-5 rounded-2xl text-center">New Analysis</a>
                    <a href="#" class="flex-1 bg-zinc-800 hover:bg-zinc-700 py-5 rounded-2xl text-center">View History</a>
                    <a href="#" class="flex-1 bg-zinc-800 hover:bg-zinc-700 py-5 rounded-2xl text-center">Upgrade Plan</a>
                </div>
            </div>

            <!-- Recent Analyses -->
            <div class="mt-16">
                <h2 class="text-2xl font-semibold mb-6">Recent Analyses</h2>
                <div class="bg-zinc-900 rounded-3xl p-8 text-zinc-400">
                    No analyses yet. Start your first one above.
                </div>
            </div>

            <!-- Contact & Account -->
            <div class="mt-20 flex justify-between text-sm">
                <a href="/contact" class="text-cyan-400 hover:text-cyan-300">About Daphne & Contact</a>
                <div class="flex gap-6">
                    <a href="#" class="text-zinc-400 hover:text-white">Edit Profile</a>
                    <a href="#" class="text-red-400 hover:text-red-300">Cancel Subscription</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)

# Placeholder routes for other pages
@app.get("/contact", response_class=HTMLResponse)
async def contact():
    return HTMLResponse("<h1 class='text-4xl text-center py-20'>Contact / About Daphne</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
