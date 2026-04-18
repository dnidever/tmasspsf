import os
import numpy as np
import requests
from astropy.table import Table
from io import BytesIO
from astropy.coordinates import SkyCoord
import subprocess
import traceback

def download(ra,dec,rad,clobber=False):

    # Query IRSA SIA service
    url = "https://irsa.ipac.caltech.edu/cgi-bin/2MASS/IM/nph-im_sia"
    params = {
        "POS": "{:.6f},{:.6f}".format(ra,dec,),
        "SIZE": "{:.3f}".format(rad)
        }
    #params = {
    #    "POS": "10.684,41.269",  # M31
    #    "SIZE": "0.1"
    #}

    response = requests.get(url, params=params)

    # Parse VOTable
    tbl = Table.read(BytesIO(response.content), format="votable")

    # Look at available images
    #print(tbl.colnames)

    # Download images
    for row in tbl:
        image_url = row['download']   # key column
        fname = image_url.split("name=")[-1]

        # Some are html files, do not download those
        # format               object     text/html  
        if row['format'] != 'image/fits':
            continue

        outfile = '/net/dl2/dnidever/2mass/images/'+fname
        if (os.path.exists(outfile) or os.path.exists(outfile+'.gz')) and clobber==False:
            print(outfile,'already exists')
            continue

        r = requests.get(image_url)
        with open(outfile, "wb") as f:
            f.write(r.content)
        # gzip
        #res = subprocess.run(['gzip','-f',outfile],shell=False)
        # The files are ALREADY gzipped
        shutil.move(outfile,outfile+'.gz')

        print("Downloaded", fname)

def downloadall(clobber=False):
    """ Download all 2MASS images in the midplane """

    # That works well because the 2MASS Atlas images are fixed-size native tiles—512×1024 pixels at 1″/pixel,
    # or 8.53′ × 17.07′—and adjacent Atlas images in a scan overlap by about 54″

    rad = 1
    larr = np.arange(-61,61+rad,rad)
    barr = np.arange(-10,10+rad,rad)

    for i in range(len(larr)):
        for j in range(len(barr)):
            coo = SkyCoord(larr[i],barr[j],unit='degree',frame='galactic')
            ra = coo.icrs.ra.degree
            dec = coo.icrs.dec.degree
            print(i+1,j+1,larr[i],barr[j])
            try:
                download(ra,dec,rad,clobber=clobber)
            except KeyboardInterrupt:
                raise
            except:
                traceback.print_exc()
