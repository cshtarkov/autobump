import sys
from setuptools import setup

if sys.version_info < (3, 5):
    sys.exit("Python 3.5+ is required for Autobump.")

setup(name="autobump",
      version="0.4.0",
      description="Automatic semantic versioning of projects",
      url="https://github.com/cshtarkov/autobump",
      author="Christian Shtarkov",
      author_email="cshtarkov@gmail.com",
      license="GPLv3",
      packages=["autobump", "autobump.handlers"],
      package_dir={"autobump": "autobump"},
      package_data={"autobump": ["libexec/*"]},
      install_requires=["javalang", "typed-ast"],
      entry_points={
          "console_scripts": ["autobump = autobump:autobump"]
      })
