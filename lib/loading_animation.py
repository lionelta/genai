#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

'''
USAGE:
    a = LoadingAnimation()
    a.run()
    # Long running code
    a.stop()
'''
import sys
import os
import itertools
import time
import threading

class LoadingAnimation:

    def __init__(self, dbpath=None):
        self._stop_animation = False
    
    def run(self, text='thinking ... '):
        self._stop_animation = False
        self._animation_thread = threading.Thread(target=self._run, args=(text,))
        self._animation_thread.start()

    def _run(self, text='thinking ... '):
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if self._stop_animation:
                break
            print(text + c, end='\r', flush=True)
            time.sleep(0.1)

    def stop(self):
        self._stop_animation = True
        

