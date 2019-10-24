from setuptools import setup, find_packages

setup(name="dash",
      package_dir={'': 'src'},
      packages=find_packages('src'),
      scripts=['scripts/dash'])
