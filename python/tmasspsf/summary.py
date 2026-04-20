import os
import numpy as np
from glob import glob
from astropy.io import fits
from astropy.wcs import WCS
from astropy.table import Table
from dlnpyutils import utils as dln,coords
from astropy.coordinates import SkyCoord

def summary():
    """ summary information """
    files = glob('/net/dl2/dnidever/2mass/images/?/*.fits.gz')
    files.sort()
    print(len(files),'2MASS images')
    dt = [('filename',str,100),('filter',str,1),('dateobs',str,50),
          ('ra',float),('dec',float),
          ('nx',int),('ny',int),('vra',float,4),('vdec',float,4),
          ('nmeas',int)]
    sumtab = np.zeros(len(files),dtype=np.dtype(dt))
    for i in range(len(files)):
        head = fits.getheader(files[i])
        sumtab['filename'][i] = os.path.basename(files[i])
        sumtab['filter'][i] = head['filter']
        utdate = head['UT_DATE']  # yymmdd format
        dateobs = '20'+utdate[:2]+'-'+utdate[2:4]+'-'+utdate[4:]+'T'+head['UT']
        sumtab['dateobs'][i] = dateobs
        sumtab['ra'][i] = head['crval1']
        sumtab['dec'][i] = head['crval2']
        nx = head['naxis1']
        ny = head['naxis2']
        sumtab['nx'][i] = nx
        sumtab['ny'][i] = ny
        w = WCS(head)
        xx = [0,nx-1,nx-1,0]
        yy = [0,0,ny-1,ny-1]
        vra,vdec = w.all_pix2world(xx,yy,0)
        sumtab['vra'][i] = vra
        sumtab['vdec'][i] = vdec
        tabfile = files[i].replace('/images/','/results/')
        if os.path.exists(tabfile):
            thead = fits.getheader(tabfile,1)
            sumtab['nmeas'][i] = thead['naxis2']
        else:
            sumtab['nmeas'][i] = -1

        print(i+1,files[i],sumtab['filter'][i],sumtab['ra'][i],
              sumtab['dec'][i],sumtab['nmeas'][i])

    sumtab = Table(sumtab)

    # Add galactic coordinates
    coo = SkyCoord(sumtab['ra'],sumtab['dec'],unit='degree',frame='icrs')
    sumtab['glon'] = coo.galactic.l.degree
    sumtab['glat'] = coo.galactic.b.degree

    #import pdb; pdb.set_trace()

    sumtab.write('/net/dl2/dnidever/2mass/tmass_summary.fits',overwrite=True)

    return sumtab
