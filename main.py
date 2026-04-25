from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import hashlib
import sqlite3
import re
import os

app = FastAPI()

# Database setup
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, trials INTEGER DEFAULT 12)''')
    conn.commit()
    conn.close()

init_db()

# Simple sessions (works on Render free tier)
sessions = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Helix Debugger Analyzer
class HelixDebugger:
    def __init__(self):
        self.patterns = {
            "memory_leak": re.compile(r"(memory.*leak|alloc.*fail|heap.*corrupt|OutOfMemory|memory.*usage)", re.IGNORECASE),
            "desync": re.compile(r"(desync|sync.*error|replication.*fail|network.*lag)", re.IGNORECASE),
            "crash": re.compile(r"(NullReference|IndexOutOfRange|Exception|crash|fatal.*error)", re.IGNORECASE),
            "race_condition": re.compile(r"(race|thread|concurrent|deadlock)", re.IGNORECASE),
            "network_spike": re.compile(r"(timeout|connection.*lost|packet.*loss|high.*latency)", re.IGNORECASE)
        }

    def analyze(self, log_text):
        findings = {}
        for bug_type, pattern in self.patterns.items():
            matches = pattern.findall(log_text)
            if matches:
                findings[bug_type] = len(matches)
        return findings

debugger = HelixDebugger()

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-zinc-950 text-white min-h-screen flex items-center justify-center">
        <div class="max-w-md w-full mx-4 bg-zinc-900 rounded-3xl p-8 text-center">
            <h1 class="text-4xl font-bold text-cyan-400 mb-2">Helix Debugger</h1>
            <p class="text-zinc-400 mb-8">AI Log Analyzer for Game Servers</p>
            <a href="/login" class="block w-full bg-cyan-500 hover:bg-cyan-600 py-4 rounded-3xl font-semibold text-xl mb-4">Login</a>
            <a href="/register" class="block w-full bg-zinc-800 hover:bg-zinc-700 py-4 rounded-3xl font-semibold text-xl">Create Account</a>
        </div>
    </body>
    </html>
    """

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return """
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-zinc-950 text-white min-h-screen flex items-center justify-center">
        <div class="max-w-md mx-auto bg-zinc-900 rounded-3xl p-8">
            <h1 class="text-3xl font-bold text-cyan-400 mb-6 text-center">Login</h1>
            <form action="/login" method="post">
                <input name="username" placeholder="Username" class="w-full bg-zinc-800 p-4 rounded-2xl mb-4" required>
                <input name="password" type="password" placeholder="Password" class="w-full bg-zinc-800 p-4 rounded-2xl mb-6" required>
                <button type="submit" class="w-full bg-cyan-500 py-4 rounded-3xl font-semibold">Login</button>
            </form>
            <a href="/register" class="text-cyan-400 text-center block mt-4">Need an account? Register</a>
        </div>
    </body></html>
    """

@app.post("/login")
async def login_post(username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0] == hash_password(password):
        sessions[username] = True
        response = RedirectResponse("/dashboard", status_code=303)
        response.set_cookie(key="user", value=username, httponly=True)
        return response
    return HTMLResponse("Invalid username or password", status_code=401)

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return """
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-zinc-950 text-white min-h-screen flex items-center justify-center">
        <div class="max-w-md mx-auto bg-zinc-900 rounded-3xl p-8">
            <h1 class="text-3xl font-bold text-cyan-400 mb-6 text-center">Create Account</h1>
            <form action="/register" method="post">
                <input name="username" placeholder="Username" class="w-full bg-zinc-800 p-4 rounded-2xl mb-4" required>
                <input name="password" type="password" placeholder="Password" class="w-full bg-zinc-800 p-4 rounded-2xl mb-6" required>
                <button type="submit" class="w-full bg-cyan-500 py-4 rounded-3xl font-semibold">Create Account</button>
            </form>
        </div>
    </body></html>
    """

@app.post("/register")
async def register_post(username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, trials) VALUES (?, ?, 12)", 
                  (username, hash_password(password)))
        conn.commit()
        sessions[username] = True
        response = RedirectResponse("/dashboard", status_code=303)
        response.set_cookie(key="user", value=username, httponly=True)
        return response
    except sqlite3.IntegrityError:
        return HTMLResponse("Username already exists", status_code=400)
    finally:
        conn.close()

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = request.cookies.get("user")
    if not user or user not in sessions:
        return RedirectResponse("/login", status_code=303)
    
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT trials FROM users WHERE username=?", (user,))
    result = c.fetchone()
    conn.close()
    trials = result[0] if result else 0

    return f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-zinc-950 text-white">
        <div class="max-w-2xl mx-auto p-8">
            <h1 class="text-4xl font-bold text-cyan-400 mb-2">Welcome back, {user}!</h1>
            <p class="text-zinc-400 mb-8">Trials remaining: <span class="text-3xl font-mono text-cyan-300">{trials}</span></p>
            
            <form action="/analyze" method="post" class="mb-8">
                <textarea name="log" rows="10" placeholder="Paste your game server log here..." 
                          class="w-full bg-zinc-900 p-6 rounded-3xl text-white"></textarea>
                <button type="submit" class="mt-6 w-full bg-cyan-500 py-5 rounded-3xl font-semibold text-xl">Analyze Log</button>
            </form>
            
            <a href="/upgrade" class="block text-center bg-zinc-800 hover:bg-zinc-700 py-4 rounded-3xl font-semibold">Upgrade for Unlimited Analyses</a>
        </div>
    </body></html>
    """

@app.post("/analyze")
async def analyze(request: Request, log: str = Form(...)):
    user = request.cookies.get("user")
    if not user or user not in sessions:
        return RedirectResponse("/login", status_code=303)
    
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT trials FROM users WHERE username=?", (user,))
    trials = c.fetchone()[0]
    
    if trials <= 0:
        conn.close()
        return HTMLResponse("No trials remaining. Please upgrade your account.", status_code=402)
    
    # Decrement trial
    c.execute("UPDATE users SET trials = trials - 1 WHERE username=?", (user,))
    conn.commit()
    conn.close()
    
    results = debugger.analyze(log)
    summary = "<br>".join([f"• {k.replace('_', ' ').title()}: {v} occurrences" for k, v in results.items()]) or "No major issues detected."
    
    return f"""
    <h1 class="text-3xl font-bold text-cyan-400 mb-4">Analysis Complete</h1>
    <div class="bg-zinc-900 p-6 rounded-3xl text-white">{summary}</div>
    <a href="/dashboard" class="mt-8 inline-block bg-cyan-500 px-8 py-4 rounded-3xl font-semibold">Back to Dashboard</a>
    """

@app.get("/upgrade", response_class=HTMLResponse)
async def upgrade_page(request: Request):
    user = request.cookies.get("user")
    if not user or user not in sessions:
        return RedirectResponse("/login", status_code=303)
    return """
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-zinc-950 text-white">
        <div class="max-w-md mx-auto mt-20 bg-zinc-900 rounded-3xl p-8 text-center">
            <h1 class="text-4xl font-bold text-cyan-400 mb-8">Upgrade Helix Debugger</h1>
            <a href="https://paypal.me/DaphneJaneGarrido/49" target="_blank" 
               class="block bg-cyan-500 hover:bg-cyan-600 py-6 rounded-3xl text-2xl font-semibold mb-6">Pro — $49/month (Unlimited)</a>
            <a href="https://paypal.me/DaphneJaneGarrido/199" target="_blank" 
               class="block bg-violet-500 hover:bg-violet-600 py-6 rounded-3xl text-2xl font-semibold">Studio — $199/month (Team + Priority)</a>
        </div>
    </body></html>
    """

# Important: No if __name__ == "__main__" block needed on Render
# Render runs the app using the Start Command you set
