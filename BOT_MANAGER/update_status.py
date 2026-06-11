"""
Auto-update CURRENT STATUS di BOT_MANAGER.md dengan data real-time dari MT5.
Jalan via Task Scheduler BotStatusUpdater tiap 15 menit.
"""

import re, subprocess, sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
MD_FILE = BASE / "BOT_MANAGER.md"


def get_status():
    bot_dir = BASE.parent / "bot_fabio"
    result = subprocess.run(
        [sys.executable, str(bot_dir / "check_status.py")],
        capture_output=True, text=True, timeout=30,
    )
    return result.stdout.strip()


def fmt_positions(status_text):
    lines = status_text.split("\n")
    balance_line = ""
    pos_parts = []
    for line in lines:
        s = line.strip()
        if "Balance:" in s:
            balance_line = s
        elif "OPEN" in s and not s.startswith("State"):
            pos_parts.append(s)
        elif "NO POSITION" in s:
            pos_parts.append(s)

    out = f"```\n{balance_line}\n"
    for s in pos_parts:
        out += s + "\n"
    out += "```"
    return out


def update_md(status_text):
    if not MD_FILE.exists():
        return

    content = MD_FILE.read_text(encoding="utf-8")
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    block = fmt_positions(status_text)

    new_section = "<!-- STATUS_START -->\n"
    new_section += f"*Auto-updated: {dt}*  \n"
    new_section += block + "\n"
    new_section += "<!-- STATUS_END -->"

    pattern = r"<!-- STATUS_START -->.*?<!-- STATUS_END -->"
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_section, content, flags=re.DOTALL)
    else:
        print("ERROR: markers not found")
        return

    MD_FILE.write_text(content, encoding="utf-8")
    print(f"Updated at {dt}")


if __name__ == "__main__":
    raw = get_status()
    update_md(raw)
