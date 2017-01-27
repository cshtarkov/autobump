from setuptools import setup

setup(name="autobump",
      version="0.1.0",
      description="Automatic semantic versioning of projects",
      url="https://github.com/cshtarkov/autobump",
      author="Christian Shtarkov",
      author_email="cshtarkov@gmail.com",
      packages=["autobump", "autobump.handlers"],
      package_dir={"autobump": "autobump"},
      package_data={"autobump": ["libexec/*"]},
      license="GPLv3",
      entry_points={
          "console_scripts": ["autobump = autobump:autobump"]
      })
