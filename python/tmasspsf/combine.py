import os
import numpy as np
from dlnpyutils import utils as dln,coords
import healpy as hp
from astropy.table import Table,vstack
from astropy.coordinates import SkyCoord
import subprocess

# Object table structure
dtobj = [('objid',str,40),('ra',float),('dec',float),('ndet',int),
         ('jmag',np.float32),('jerr',np.float32),('ndetj',int),
         ('hmag',np.float32),('herr',np.float32),('ndeth',int),
         ('kmag',np.float32),('kerr',np.float32),('ndetk',int),
         ('chi',np.float32),('sharp',np.float32)]

def mergemeastoobj(obj,meas,filt):
    """ Add new measurements to object table. """

    # Keep the objid of the first measurement
    lfilt = filt.lower()

    # Update columns
    # all of these must have detections in SOME band
    # -ra/dec
    # -ndet
    # -chi/sharp
    cols = ['ra','dec','chi','sharp']
    ndet = obj['ndet']
    for c in cols:
        oldval = obj[c]
        # This was previously averaged
        # multiply by (previous) ndet to get the sum
        # then add the new value, and new average
        sumval = oldval*ndet
        mval = meas[c]
        newval = (sumval+mval)/(ndet+1)
        obj[c] = newval
    # Update ndet
    obj['ndet'] += 1

    # Same for the magnitude
    # -Xmag/Xerr/ndetX
    ndetX = obj['ndet'+lfilt]

    # Index for first detections for this band
    # or multiple detections
    multi = np.where(ndetX > 0)
    first = np.arange(len(obj))
    if len(multi)>0 and len(multi)==len(obj):
        first = []
    elif len(multi)>0 and len(multi)<len(obj):
        first = np.delete(first,multi)

    # multiple detections to average
    if len(multi)>0:
        # add in flux space
        oldmag = obj[lfilt+'mag'][multi]
        oldflux = 10**(-0.4*oldmag)  # convert to flux
        sumflux = oldflux*ndetX[multi]
        mmag = meas['mag'][multi]
        mflux = 10**(-0.4*mmag)      # convert to flux
        newflux = (sumflux+mflux)/(ndetX[multi]+1)
        newmag = -2.5*np.log10(newflux)
        obj[lfilt+'mag'][multi] = newmag

        # Same for the mag uncertainty
        # add them in quadrature
        # err = sqrt(err1**2+err2**2)
        ndetX = obj['ndet'+lfilt][multi]
        olderr = obj[lfilt+'err'][multi]
        oldsum2 = olderr**2
        merr = meas['err'][multi]
        newerr = np.sqrt(oldsum2+merr**2)
        obj[lfilt+'err'][multi] = newerr
    
    # first/single detections to add
    if len(first)>0:
        obj[lfilt+'mag'][first] = meas['mag'][first]
        obj[lfilt+'err'][first] = meas['err'][first]

    # Increment ndetX
    obj['ndet'+lfilt] += 1

    return obj

def meastoobj(meas,filt):
    """ Create object table rows from measurement table. """
    newobj = np.zeros(len(meas),dtype=np.dtype(dtobj))
    newobj['ra'] = meas['ra']
    newobj['objid'] = meas['objid']  # J_1518861_990723s_097_0115.1090
    newobj['dec'] = meas['dec']
    newobj['ndet'] = 1
    for c in ['jmag','jerr','hmag','herr','kmag','kerr']:
        newobj[c] = np.nan
    newobj['chi'] = meas['chi']
    newobj['sharp'] = meas['sharp']
    newobj[filt.lower()+'mag'] = meas['mag']
    newobj[filt.lower()+'err'] = meas['err']
    return newobj

def combinehealpix(meta):
    """ input meta information for images to combine. """

    nfiles = len(meta)
    dcr = 1.0

    # How this works:
    # loop over each exposure
    # -cross-match to existing objects
    # -combine 

    obj = []
    for i in range(nfiles):
        print(i+1,meta['filename'][i],meta['nmeas'][i])
        filt = meta['filter'][i]
        filename = '/net/dl2/dnidever/2mass/results/'+filt.upper()+'/'+meta['filename'][i]
        if os.path.exists(filename)==False:
            print(filename,'NOT FOUND')
            continue
        meas1 = Table.read(filename)
        nmeas1 = len(meas1)

        if len(obj)==0:
            obj = meastoobj(meas1,filt)
        else:
            # 1) xmatch obj and meas1
            mind,oind,dist = coords.xmatch(meas1['ra'],meas1['dec'],
                                           obj['ra'],obj['dec'],dcr,unique=True)            
            nmatch = len(mind)
            print(' ',nmatch,'matches to object table')
            # 2) combine information for matches
            if nmatch>0:
                objtomerge = obj[oind]
                meastomerge = meas1[mind]
                newobj = mergemeastoobj(objtomerge,meastomerge,filt)
                obj[oind] = newobj
            # 3) Add leftover measurements to object table
            leftind = np.arange(nmeas1)
            if nmatch>0 and nmatch<nmeas1:
                leftind = np.delete(leftind,mind)
            elif nmatch>0 and nmatch==nmeas1:
                leftind = []
            nleft = len(leftind)
            if nleft>0:
                print('  Adding',nleft,'sources to object table')
                newobj = meastoobj(meas1[leftind],filt)
                obj = np.concatenate((obj,newobj))

    return obj

def combine():
    """ Combine all healpix """

    nside = 32
    npix = hp.nside2npix(nside)
    pixsize = hp.nside2resol(nside,arcmin=True)/60.0
    sumtab = Table.read('/net/dl2/dnidever/2mass/tmass_summary.fits')

    hdt = [('pix',int),('ra',float),('dec',float),
           ('glon',float),('glat',float),('nimages',int)]
    htab = np.zeros(npix,dtype=np.dtype(hdt))
    htab['nimages'] = -1

    # Loop over all possible healpix
    fmt = '{:5d} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:5d}'
    for ipix in range(npix):
        # Do any of the images overlap
        cenra,cendec = hp.pix2ang(nside,ipix,lonlat=True)
        coo = SkyCoord(cenra,cendec,unit='degree',frame='icrs')
        glon = coo.galactic.l.degree
        if glon>180:
            glon -= 360
        glat = coo.galactic.b.degree
        htab['pix'][ipix] = ipix
        htab['ra'][ipix] = cenra
        htab['dec'][ipix] = cendec
        htab['glon'][ipix] = glon
        htab['glat'][ipix] = glat
        if np.abs(glon) > 65 or np.abs(glat)>12:
            print(fmt.format(ipix,cenra,cendec,glon,glat,0))
            continue
        #ind1,ind2,dist = coords.xmatch([cenra],[cendec],sumtab['ra'],
        #                               sumtab['dec'],3600)
        dist = coords.sphdist(cenra,cendec,sumtab['ra'],sumtab['dec'])
        ind, = np.where(dist < 3)
        htab['nimages'][ipix] = len(ind)
        if len(ind)==0:
            print(fmt.format(ipix,cenra,cendec,glon,glat,0))
            continue

        # Do more rigorous overlap checking with vertices
        # vra, vdec
        vec = hp.boundaries(nside, ipix, step=1, nest=False) 
        hra,hdec = hp.vec2ang(vec.T,lonlat=True)
        # ADD A BUFFER!!!!!
        overlaps = np.zeros(len(ind),bool)
        for j in range(len(ind)):
            vra = sumtab['vra'][ind[j]]
            vdec = sumtab['vdec'][ind[j]]
            olap = coords.doPolygonsOverlap(hra,hdec,vra,vdec)
            overlaps[j] = olap
        gd, = np.where(overlaps)
        if len(gd)==0:
            print(fmt.format(ipix,cenra,cendec,glon,glat,len(gd)))
            htab['nimages'][ipix] = 0
            continue
        ind = ind[gd]
        htab['nimages'][ipix] = len(ind)
        print(fmt.format(ipix,cenra,cendec,glon,glat,len(ind)))


        # Now combine them
        meta = sumtab[ind]
        obj = combinehealpix(meta)

        # Save the catalogs
        outfile = '/net/dl2/dnidever/2mass/combine/'+str(ipix)+'.fits'
        print('Writing to',outfile)
        Table(obj).write(outfile,overwrite=True)
        res = subprocess.run(['gzip','-f',outfile],shell=False)

        #import pdb; pdb.set_trace()

    import pdb; pdb.set_trace()
