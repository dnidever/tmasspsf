#!/usr/bin/env python

from distutils.core import setup

setup(name='tmasspsf',
      version='1.0.0',
      description='2MASS PSF photometry',
      author='David Nidever',
      author_email='dnidever@montana.edu',
      url='https://github.com/dnidever/tmasspsf',
      packages=['tmasspsf'],
      package_dir={'':'python'},
      #package_data={'ukidss': ['data/*','data/params/*','data/params/*/*']},
      scripts=['bin/tmasspsf','bin/runtmasspsf'],
      #         'bin/ukidss_measure','bin/ukidss_calibrate',
      #         'bin/ukidss_calibrate_healpix','bin/ukidss_combine'],
      ##py_modules=['nsc_instcal',''],
      requires=['numpy','astropy','scipy','dlnpyutils','sep','healpy','dustmaps','astroquery'],
      #include_package_data=True
)
