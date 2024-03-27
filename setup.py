from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in petropipe/__init__.py
from petropipe import __version__ as version

setup(
	name="petropipe",
	version=version,
	description="Petropipe Customization",
	author="Wahni IT Solutions",
	author_email="info@wahni.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
