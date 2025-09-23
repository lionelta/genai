#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

'''
This is a python library which helps capture usage logs for the GenAI project.

Here's the specification:
1. The library will take in 2 arguments:
    - `log_file`: The file where the logs will be stored.
    - `data`: a dictionary containing the data to be logged.

2. the library will log the data in the following JSON format:
{
    "timestamp": "2023-10-01T12:00:00Z",
    "user": "lionelta",
    "host": "ascy00060.sc.altera.com",
    "data": {
        "key1": "value1",
        "key2": "value2"
    }
    ### the full cmdline of each process in the stack trace 
    "stack": ['the full cmdline of each process in the stack trace',
              '/bin/tcsh -f '
              '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/bin/_cmxsetupclean /nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/bin/cmx.py seal generate -i bbb',
              '/bin/tcsh -f /nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/bin/dmx seal generate -i bbb',
              '-usr/intel/bin/tcsh',
              '/usr/bin/X11/konsole',
              'kded5 [kdeinit5] ',
              'kdeinit5: Running... ',
              '/usr/lib/systemd/systemd --switched-root --system --deserialize 23']
    
    ],
}
'''
import sys
import os
import argparse
import logging
import psutil
import json
import warnings
import shlex
from datetime import datetime
warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

ROOTDIR = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main'

class UsageLog:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.info = {}

    def write_log(self, logdir, data, extra_yyyymm_dir=True):
        ''' Write the usage log to a file in the specified directory.
        logfilename = <yymmdd_hhmmss>_<user>_<hostname>_<pid>.json
        if extra_yyyymm_dir is True, the log file will be stored in a subdirectory named <yyyymm> under logdir.
        '''
        self.info['timestamp'] = self.get_timestamp()
        self.info['data'] = data
        self.info['cmdline'] = self.get_process_cmdline()
        self.info['user'] = os.getenv('USER', 'unknown_user')
        self.info['host'] = os.uname().nodename
        self.info['version'] = os.path.basename(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

        ### Make sure logdir is group writable
        try:
            os.system('mkdir -p ' + logdir)
            os.system(f'chmod -f 777 {logdir}')
        except Exception as e:
            pass
        if extra_yyyymm_dir:
            '''
            yyyymm = self.info['timestamp'][:7].replace('-', '')
            logdir = os.path.join(logdir, yyyymm)
            '''
            ### Change the folder from yyyymm to <yyyy>WW<ww>
            workweek = datetime.now().isocalendar()[1]
            yyyyww = f"{self.info['timestamp'][:4]}WW{workweek:02d}"
            logdir = os.path.join(logdir, yyyyww)
        ### mkdir to ensure logdir exists
        try:
            os.system('mkdir -p ' + logdir)
            os.system('chmod -f 777 ' + logdir)
        except Exception as e:
            self.logger.error(f"Failed to create UsageLog directory {logdir}: {e}")
            return

        yymmdd_hhmmss = self.info['timestamp'].replace('-', '').replace(':', '').replace('T', '_').replace('Z', '')
        logfilename = f"{yymmdd_hhmmss}_{self.info['user']}_{self.info['host']}_{os.getpid()}.json"
        logfilepath = os.path.join(logdir, logfilename)

        try:
            with open(logfilepath, 'w') as f:
                ### dump pretty format
                json.dump(self.info, f, indent=4)
                f.write('\n')
            self.logger.debug(f"Log written to {logfilepath}")
            os.system("chmod -f 777 " + logfilepath)
        except Exception as e:
            self.logger.error(f"Failed to write UsageLog: {e}")
            return

    def get_timestamp(self):
        return datetime.utcnow().isoformat() + 'Z'

    def get_process_cmdline(self):
        return ' '.join([shlex.quote(c) for c in psutil.Process().cmdline()])

    def get_stack_trace_cmdline(self):
        return [' '.join(x.cmdline()) for x in psutil.Process().parents()]



if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    sys.exit(main())

