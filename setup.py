# -*- coding: utf-8 -*-

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
     name='mlsuite',
     version='0.1.3.4',
     scripts=[] ,
     author="Adrián Javaloy",
     author_email="adrian.javaloy@gmail.com",
     description="A framework to ease Machine Learning development.",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/adrianjav/ml-code-base",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3.7",
         # "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
     include_package_data=True,
     install_requires=[
         'dotmap',
         'pyyaml',
         'click',
     ]
)
