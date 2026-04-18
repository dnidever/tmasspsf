import os
import numpy as np
from glob import glob
from dlnpyutils import utils as dln,job_daemon as jd

script = '/home/dnidever/projects/tmasspsf/bin/tmasspsf'
outdir = '/net/dl2/dnidever/2mass/results/'
files = glob('/net/dl2/dnidever/2mass/images/*.fits.gz')
files.sort()
np.random.seed(0)
np.random.shuffle(files)
cmds = np.zeros(len(files),(str,100))
dirs = np.zeros(len(files),(str,200))
for i in range(len(files)):
    file1 = files[i]
    cmd = script+' '+file1
    cmds[i] = cmd
    dirs[i] = outdir
jobs = jd.job_daemon(cmds,dirs,nmulti=10,prefix='tmpsf',hyperthread=True)

