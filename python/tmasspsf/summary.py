import os
import numpy as np
from glob import glob
from astropy.io import fits

def summary():
    """ summary information """
    files = glob('/net/dl2/dnidever/2mass/images/*.fits.gz')
    files.sort()
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
        sumtab['nx'][i] = head['naxis1']
        sumtab['ny'][i] = head['naxis2']
        w = WCS(head)
        xx = [0,nx-1,nx-1,0]
        yy = [0,0,ny-1,ny-1]
        vra,vdec = w.all_pix2world(xx,yy,0)
        sumtab['vra'][i] = vra
        sumtab['vdec'][i] = vdec
        tabfile = files[i].replace('/images/','/results/').replace()
        thead = fits.getheader(tabfile,1)
        sumtab['nmeas'][i] = thead['naxis2']

        import pdb; pdb.set_trace()

    import pdb; pdb.set_trace()
