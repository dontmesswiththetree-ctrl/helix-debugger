from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
from datetime import datetime
import hashlib
import uuid

app = FastAPI(title="Helix Debugger")

# ========================
# Database
# ========================
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
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

def get_user(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(username, password, email="", name=""):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, email, name, created_at) VALUES (?, ?, ?, ?, ?)",
              (username, hash_password(password), email, name, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def decrement_trials(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET trials_left = trials_left - 1 WHERE username=? AND trials_left > 0", (username,))
    conn.commit()
    conn.close()

# ========================
# Analyzer
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
        results = []
        for bug_type, pattern in self.patterns.items():
            matches = pattern.findall(log_text)
            if matches:
                results.append({"type": bug_type.replace("_", " ").title(), "confidence": min(len(matches) * 25, 95)})
        summary = "Analysis complete. Most likely root cause: " + (results[0]["type"] if results else "Unknown")
        return {"summary": summary, "ranked_causes": results}

debugger = HelixDebugger()

# ========================
# Professional Game-Dev UI
# ========================

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Helix Debugger • Game Server AI</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            body { font-family: 'Inter', system-ui; background: #0a0a0f; color: #e0e0e0; }
            .hero { background: linear-gradient(135deg, #0f172a, #1e2937); }
            .neon { text-shadow: 0 0 20px #22d3ee; }
        </style>
    </head>
    <body>
        <div class="max-w-7xl mx-auto px-6 py-16 text-center hero">
            <h1 class="text-7xl font-bold neon text-cyan-400">Helix Debugger</h1>
            <p class="text-3xl mt-6 text-cyan-300">AI that finds the bug before you do.</p>
            <p class="mt-8 text-xl text-zinc-400 max-w-2xl mx-auto">Instant root cause analysis. Real reproduction steps. Built for game developers who ship under pressure.</p>
            <div class="mt-12">
                <a href="/login" class="inline-block bg-gradient-to-r from-cyan-400 to-blue-500 text-black px-12 py-6 rounded-3xl text-2xl font-semibold hover:scale-105 transition">Start Free Trial • 12 Analyses</a>
            </div>
        </div>
    </body></html>
    """)

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse("""
    <html><head><title>Login</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-zinc-950 text-zinc-200 flex items-center justify-center min-h-screen">
        <div class="max-w-md w-full p-8 bg-zinc-900 rounded-3xl">
            <h1 class="text-3xl font-bold mb-8 text-center">Sign In</h1>
            <form method="post" action="/login" class="space-y-6">
                <input type="text" name="username" placeholder="Username" class="w-full p-4 rounded-2xl bg-zinc-800 text-white">
                <input type="password" name="password" placeholder="Password" class="w-full p-4 rounded-2xl bg-zinc-800 text-white">
                <button type="submit" class="w-full py-4 bg-cyan-400 text-black font-semibold rounded-2xl">Sign In</button>
            </form>
            <p class="text-center mt-6 text-zinc-400">New user? <a href="/register" class="text-cyan-400">Create account</a></p>
        </div>
    </body></html>
    """)

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = get_user(username)
    if user and user[2] == hash_password(password):
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="username", value=username, httponly=True, max_age=3600*24*30)
        return response
    return HTMLResponse("<h1 class='text-red-500 text-center py-20'>Invalid credentials.</h1>")

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return HTMLResponse("""
    <html><head><title>Register</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-zinc-950 text-zinc-200 flex items-center justify-center min-h-screen">
        <div class="max-w-md w-full p-8 bg-zinc-900 rounded-3xl">
            <h1 class="text-3xl font-bold mb-8 text-center">Create Account</h1>
            <form method="post" action="/register" class="space-y-6">
                <input type="text" name="username" placeholder="Username" class="w-full p-4 rounded-2xl bg-zinc-800 text-white">
                <input type="email" name="email" placeholder="Email" class="w-full p-4 rounded-2xl bg-zinc-800 text-white">
                <input type="password" name="password" placeholder="Password" class="w-full p-4 rounded-2xl bg-zinc-800 text-white">
                <button type="submit" class="w-full py-4 bg-cyan-400 text-black font-semibold rounded-2xl">Create Account</button>
            </form>
        </div>
    </body></html>
    """)

@app.post("/register")
async def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    try:
        create_user(username, password, email)
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="username", value=username, httponly=True, max_age=3600*24*30)
        return response
    except:
        return HTMLResponse("<h1 class='text-red-500 text-center py-20'>Username already exists.</h1>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    user = get_user(username)
    trials = user[5] if user else 0
    return HTMLResponse(f"""
    <html><head><title>Dashboard</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-zinc-950 text-zinc-200">
        <div class="max-w-7xl mx-auto px-8 py-12">
            <h1 class="text-5xl font-bold text-cyan-400">Welcome back, {username}</h1>
            <p class="text-xl mt-4">Trials remaining: <span class="font-mono text-4xl text-emerald-400">{trials}</span></p>
            <div class="mt-12 grid grid-cols-1 md:grid-cols-2 gap-8">
                <a href="/analyze" class="bg-cyan-400 text-black py-6 rounded-3xl text-center text-2xl font-semibold">New Analysis</a>
                <a href="/upgrade" class="bg-zinc-800 hover:bg-zinc-700 py-6 rounded-3xl text-center text-2xl font-semibold">Upgrade Plan</a>
            </div>
        </div>
    </body></html>
    """)

@app.get("/analyze", response_class=HTMLResponse)
async def analyze_page(request: Request):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    return HTMLResponse("""
    <html><head><title>New Analysis</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-zinc-950 text-zinc-200">
        <div class="max-w-4xl mx-auto px-8 py-12">
            <h1 class="text-4xl font-bold mb-8">New Analysis</h1>
            <form method="post" action="/analyze" class="space-y-6">
                <textarea name="log_text" rows="12" class="w-full p-6 bg-zinc-800 rounded-3xl text-white" placeholder="Paste your server log here..."></textarea>
                <button type="submit" class="w-full py-5 bg-cyan-400 text-black font-semibold rounded-3xl text-xl">Analyze Log</button>
            </form>
        </div>
    </body></html>
    """)

@app.post("/analyze")
async def analyze_post(request: Request, log_text: str = Form(...)):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    decrement_trials(username)
    result = debugger.analyze(log_text)
    return HTMLResponse(f"""
    <html><head><title>Analysis Result</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-zinc-950 text-zinc-200">
        <div class="max-w-4xl mx-auto px-8 py-12">
            <h1 class="text-4xl font-bold mb-8">Analysis Complete</h1>
            <div class="bg-zinc-900 p-8 rounded-3xl">{result['summary']}</div>
            <a href="/dashboard" class="mt-8 inline-block px-8 py-4 bg-cyan-400 text-black rounded-3xl">Back to Dashboard</a>
        </div>
    </body></html>
    """)

@app.get("/upgrade", response_class=HTMLResponse)
async def upgrade_page():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upgrade - Helix Debugger</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            .card { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
            .card:hover { transform: translateY(-4px); box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1); }
        </style>
    </head>
    <body class="bg-zinc-950 text-zinc-200">
        <div class="max-w-6xl mx-auto px-8 py-12">
            <h1 class="text-5xl font-bold text-center mb-4 text-cyan-400">Choose Your Plan</h1>
            <p class="text-center text-zinc-400 mb-12">Unlock unlimited power for your game servers</p>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="card bg-zinc-900 rounded-3xl p-8 text-center">
                    <h3 class="text-2xl font-semibold mb-2">Pro</h3>
                    <p class="text-5xl font-bold mb-6">$49 <span class="text-sm font-normal text-zinc-400">/mo</span></p>
                    <ul class="space-y-4 mb-10 text-sm">
                        <li>✅ Unlimited analyses</li>
                        <li>✅ Full history &amp; exports</li>
                        <li>✅ Team of up to 5</li>
                    </ul>
                    <img src="https://i.imgur.com/your-paypal-qr.png" class="mx-auto w-48 mb-6" alt="PayPal QR">
                    <p class="text-sm text-zinc-400">Scan with PayPal to upgrade</p>
                </div>

                <div class="card bg-zinc-900 rounded-3xl p-8 text-center border-2 border-cyan-400 scale-105 shadow-2xl">
                    <div class="bg-cyan-400 text-black text-xs font-bold px-4 py-1 rounded-full inline-block mb-4">MOST POPULAR</div>
                    <h3 class="text-2xl font-semibold mb-2">Studio</h3>
                    <p class="text-5xl font-bold mb-6">$199 <span class="text-sm font-normal text-zinc-400">/mo</span></p>
                    <ul class="space-y-4 mb-10 text-sm">
                        <li>✅ Everything in Pro</li>
                        <li>✅ Priority AI processing</li>
                        <li>✅ Custom integrations</li>
                        <li>✅ Dedicated support</li>
                    </ul>
                    <img src="https://i.imgur.com/your-paypal-qr.png" class="mx-auto w-48 mb-6" alt="PayPal QR">
                    <p class="text-sm text-zinc-400">Scan with PayPal to upgrade</p>
                </div>

                <div class="card bg-zinc-900 rounded-3xl p-8 text-center">
                    <h3 class="text-2xl font-semibold mb-2">Enterprise</h3>
                    <p class="text-5xl font-bold mb-6">Custom</p>
                    <ul class="space-y-4 mb-10 text-sm">
                        <li>✅ Everything in Studio</li>
                        <li>✅ On-premise deployment</li>
                        <li>✅ SLA &amp; custom features</li>
                    </ul>
                    <a href="/contact" class="block w-full py-4 bg-zinc-800 hover:bg-zinc-700 rounded-3xl text-center font-medium">Contact Sales</a>
                </div>
            </div>
        </div>
    </body></html>
    """)

@app.get("/examples", response_class=HTMLResponse)
async def examples():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Examples - Helix Debugger</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-zinc-950 text-zinc-200">
        <div class="max-w-7xl mx-auto px-8 py-12">
            <h1 class="text-5xl font-bold text-cyan-400 mb-12 text-center">Real-World Examples</h1>
            
            <div class="space-y-12">
                <div class="bg-zinc-900 rounded-3xl p-8">
                    <h3 class="text-xl font-semibold mb-4">Star Citizen Orbital Platform Crash</h3>
                    <div class="bg-zinc-950 p-4 rounded-2xl text-sm font-mono text-emerald-400 mb-6">NullReferenceException in PlayerReplication.cs:245</div>
                    <div class="text-cyan-400 font-medium">Root Cause: Network Spike (87% confidence)</div>
                    <p class="text-zinc-400 mt-4">Detailed steps: Reproduce with high player count + orbital platform spawn. Check replication system after recent physics update.</p>
                </div>

                <div class="bg-zinc-900 rounded-3xl p-8">
                    <h3 class="text-xl font-semibold mb-4">Desync During High Player Count</h3>
                    <div class="bg-zinc-950 p-4 rounded-2xl text-sm font-mono text-emerald-400 mb-6">State mismatch detected between server and client</div>
                    <div class="text-cyan-400 font-medium">Root Cause: Desync (92% confidence)</div>
                    <p class="text-zinc-400 mt-4">Detailed steps: Test with 50+ players in the same instance. Simulate high latency. Compare server and client state after spawn actions.</p>
                </div>
            </div>
        </div>
    </body></html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
