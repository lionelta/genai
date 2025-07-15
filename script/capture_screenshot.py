#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

import sys
import os
import subprocess

if len(sys.argv) < 2 or '-h' in ' '.join(sys.argv):
    print("Usage: capture_screenshot.py [--active | --screen]")
    print("Options:")
    print("  --active : Capture screenshot of the currently active window")
    print("  --screen : Capture screenshot of the entire screen")
    print("  --manual : Capture screenshot from user bbox selection")
    sys.exit(1)

if '--active' in sys.argv:
    cmd = """xprop -root _NET_ACTIVE_WINDOW | awk '{print $NF}'"""
    window = subprocess.getoutput(cmd).strip()
elif '--screen' in sys.argv:
    window = 'root'
elif '--manual' in sys.argv:
    window = None

print(f"window: {window}")
if window:
    cmd = f"import -window {window} screenshot.jpeg"
else:
    cmd = "import screenshot.jpeg"
os.system(cmd)
print("Screenshot saved as screenshot.jpeg")

