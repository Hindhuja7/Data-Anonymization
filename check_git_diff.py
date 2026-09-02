import subprocess, os

ws_dir = r"C:\Users\lokin\.gemini\antigravity\scratch\Data-Anonymization"
log_path = os.path.join(ws_dir, "git_output.txt")

v = subprocess.run(["git", "--version"], cwd=ws_dir, capture_output=True, text=True)
s = subprocess.run(["git", "status"], cwd=ws_dir, capture_output=True, text=True)
l = subprocess.run(["git", "log", "-n", "3", "--oneline"], cwd=ws_dir, capture_output=True, text=True)
d = subprocess.run(["git", "diff", "--stat"], cwd=ws_dir, capture_output=True, text=True)

with open(log_path, "w", encoding="utf-8") as f:
    f.write(f"GIT VERSION: {v.stdout.strip()}\n\n")
    f.write(f"GIT STATUS:\n{s.stdout}\n\n")
    f.write(f"GIT LOG:\n{l.stdout}\n\n")
    f.write(f"GIT DIFF:\n{d.stdout}\n\n")

if os.path.exists(os.path.join(ws_dir, "powershell.cmd")):
    try:
        os.remove(os.path.join(ws_dir, "powershell.cmd"))
    except Exception:
        pass
