import os
import numpy as np
from astropy.io import fits
from astropy.table import Table,vstack
from dlnpyutils import utils as dln
from datetime import datetime

def prep(filename):
    hdu = fits.open(filename)
    # Fix NaNs
    # add RDNOISE, GAIN
    data = hdu[0].data
    head = hdu[0].header
    hdu.close()
    bad = (~np.isfinite(data) | (data<0))
    newdata = data.copy().astype(np.float32)
    newhead = head.copy()
    newdata[bad] = 65000

    newhead['BITPIX'] = -32
    newhead['SATURATE'] = 64000
    #newhead['FILTER'] = 'j'

    # images are in ADU

    # North, 1997-05-21 to 1998-06-04: gain J/H/Ks = 10.0 / 10.0 / 8.0 e⁻/DN; read noise = 40 / 40 / 56 e⁻
    # North, 1998-06-05 to 1998-09-16: 10.0 / 10.0 / 8.0; 42 / 40 / 57
    # North, 1998-09-19 to 1998-10-23: 10.0 / 10.0 / 8.0; 42 / 40 / 57
    # North, 1998-10-24 to 1999-07-23: 10.0 / 8.0 / 6.5; 44 / 50 / 54
    # North, 1999-09-13 to end: 7.9 / 9.4 / 8.7; 38 / 42 / 44
    # South, 1998-03-18 to 1999-02-26: 8.5 / 8.0 / 9.9; 43 / 45 / 45
    # South, 1999-03-01 to end: 6.8 / 7.7 / 10.0; 45 / 41 / 50.
    
    utdate = head['UT_DATE']  # yymmdd format
    dateobs = '20'+utdate[:2]+'-'+utdate[2:4]+'-'+utdate[4:]+'T'+head['UT']

    # South
    if head['TELNAME']=='CTIO':
        # South, 1998-03-18 to 1999-02-26: 8.5 / 8.0 / 9.9; 43 / 45 / 45
        if datetime.fromisoformat(dateobs) < datetime(1999,2,26):
            gaindict = {'j':8.5,'h':8.0,'k':9.9}
            noisedict = {'j':43.0,'h':45.0,'k':45.0}
        # South, 1999-03-01 to end: 6.8 / 7.7 / 10.0; 45 / 41 / 50.
        else:
            gaindict = {'j':6.8,'h':7.7,'k':10.0}
            noisedict = {'j':45.0,'h':41.0,'k':50.0}
    # North
    else:
        # North, 1997-05-21 to 1998-06-04: gain J/H/Ks = 10.0 / 10.0 / 8.0 e⁻/DN; read noise = 40 / 40 / 56 e⁻
        if datetime.fromisoformat(dateobs) < datetime(1998,6,4):
            gaindict = {'j':10.0,'h':10.0,'k':8.0}
            noisedict = {'j':40.0,'h':40.0,'k':56.0}
        # North, 1998-06-05 to 1998-09-16: 10.0 / 10.0 / 8.0; 42 / 40 / 57
        elif datetime.fromisoformat(dateobs) < datetime(1998,9,16):
            gaindict = {'j':10.0,'h':10.0,'k':8.0}
            noisedict = {'j':42.0,'h':40.0,'k':57.0}
        # North, 1998-09-19 to 1998-10-23: 10.0 / 10.0 / 8.0; 42 / 40 / 57
        elif datetime.fromisoformat(dateobs) < datetime(1998,10,23):
            gaindict = {'j':10.0,'h':10.0,'k':8.0}
            noisedict = {'j':42.0,'h':40.0,'k':57.0}
        # North, 1998-10-24 to 1999-07-23: 10.0 / 8.0 / 6.5; 44 / 50 / 54
        elif datetime.fromisoformat(dateobs) < datetime(1999,7,23):
            gaindict = {'j':10.0,'h':8.0,'k':6.5}
            noisedict = {'j':44.0,'h':50.0,'k':54.0}
        # North, 1999-09-13 to end: 7.9 / 9.4 / 8.7; 38 / 42 / 44
        else:
            gaindict = {'j':7.9,'h':9.4,'k':8.7}
            noisedict = {'j':38.0,'h':42.0,'k':44.0}

    filt = head['filter']
    gain = gaindict[filt]
    noise = noisedict[filt]
    newhead['GAIN'] = gain
    newhead['RDNOISE'] = noise
    print('filename',filename)
    print('filter=',filt)
    print('gain=',gain)
    print('rdnoise=',noise)
    print('sky=',head['skyval'])
    print('skysig=',head['skysig'])

    # SKYVAL  =          222.6468201 /   GFIND Sky Estimate                           
    # SKYSIG  =          2.677612305 /   Grid  Noise Estimate  
    med = np.nanmedian(data)
    sig = dln.mad(data)
    print('med=',med)
    print('sig=',sig)

    newfilename = filename.replace('.fits','_dao.fits')
    print('Writing to',newfilename)
    fits.writeto(newfilename,newdata,newhead,overwrite=True)

def mkopt(filename):
    pass
