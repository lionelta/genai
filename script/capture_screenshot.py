#!/usr/bin/env python

import sys
import os
import subprocess

if len(sys.argv) < 2 or '-h' in ' '.join(sys.argv):
    print("Usage: capture_screenshot.py [--active | --screen]")
    print("Options:")
    print("  --active : Capture screenshot of the currently active window")
    print("  --screen : Capture screenshot of the entire screen")
    sys.exit(1)

if '--active' in sys.argv:
    cmd = """xprop -root _NET_ACTIVE_WINDOW | awk '{print $NF}'"""
    window = subprocess.getoutput(cmd).strip()
elif '--screen' in sys.argv:
    window = 'root'

print(f"window: {window}")
cmd = f"import -window {window} screenshot.jpeg"
os.system(cmd)
print("Screenshot saved as screenshot.jpeg")

