import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
     name='mlsuite',
     version='0.1',
     scripts=[] ,
     author="Adrián Javaloy Bornás",
     author_email="adrian.javaloy@gmail.com",
     description="A framework to ease Machine Learning development.",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/adrianjav/ml-code-base",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3.7",
#         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
    data_files=[('mlsuite', ['mlsuite/config.yaml'])]
 )
