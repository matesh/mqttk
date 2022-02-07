from setuptools import setup
from mqttk import __version__

url = "https://github.com/matesh/mqttk"
readme = open('README.md').read()

APP = ['mqttk_entry.py']
DATA_FILES = [('', ['mqttk'])]
OPTIONS = {'iconfile':'mqttk.icns',
           'plist': {
                'CFBundleDevelopmentRegion': 'English',
                'CFBundleIdentifier': "com.mateszabo.mqttk",
                'CFBundleVersion': "0.1.0",
                'NSHumanReadableCopyright': u"Mate Szabo"
                }
           }

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name="mqttk",
    packages=["mqttk"],
    version=__version__,
    long_description=readme,
    long_description_content_type='text/markdown',
    include_package_data=True,
    author="Mate Szabo",
    author_email="mate@mateszabo.com",
    maintainer='Mate Szabo',
    maintainer_email='mate@mateszabo.com',
    description="An MQTT client GUI written in pure python, resembles MQTT.fx",
    url=url,
    install_requires=[
        "paho-mqtt",
    ],
    package_data={
        'mqttk': ['*.png']
    },
    entry_points={
        'gui_scripts': ['mqttk=mqttk.__main__:main'],
        'console_scripts': ['mqttk-console=mqttk.__main__:main']
    },
    download_url="{}/tarball/{}".format(url, __version__),
    license="GPLv3"
)
