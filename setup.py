from setuptools import setup, find_packages
from mqttk import __version__

url = "https://github.com/matesh/mqttk"
readme = open('README.md').read()

setup(
    name="mqttk",
    packages=find_packages(),
    version=__version__,
    long_description=readme,
    long_description_content_type='text/markdown',
    include_package_data=True,
    author="Mate Szabo",
    author_email="mate@mateszabo.com",
    maintainer='Mate Szabo',
    maintainer_email='mate@mateszabo.com',
    description="A lightweight MQTT client GUI written in pure python",
    url=url,
    python_requires=">=3.7",
    install_requires=[
        "paho-mqtt",
        "xmltodict"
    ],
    entry_points={
        'gui_scripts': ['mqttk=mqttk.__main__:main'],
        'console_scripts': ['mqttk-console=mqttk.__main__:main']
    },
    package_data={
        'mqttk': ['*.png']
    },
    download_url="{}/releases".format(url),
    license="GPLv3"
)
