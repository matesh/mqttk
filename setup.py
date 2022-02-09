from setuptools import setup
from mqttk import __version__
import sys

url = "https://github.com/matesh/mqttk"
readme = open('README.md').read()
#
# if sys.platform == "darwin" and "py2app" in sys.argv:
#     extra_options = dict(
#         app=['mqttk_entry.py'],
#         data_files=[('', ['mqttk'])],
#         setup_requires=['py2app'],
#         options=dict(
#             py2app={
#                     'iconfile':'mqttk.icns',
#                     'plist': {
#                                 'CFBundleDevelopmentRegion': 'English',
#                                 'CFBundleIdentifier': "com.mateszabo.mqttk",
#                                 'CFBundleVersion': __version__,
#                                 'NSHumanReadableCopyright': u"Mate Szabo"
#                     }
#             }
#         )
#     )
# else:
#     extra_options = dict(
#
#     )


setup(
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
    description="A lightweight MQTT client GUI written in pure python",
    url=url,
    install_requires=[
        "paho-mqtt",
    ],
    entry_points={
        'gui_scripts': ['mqttk=mqttk.__main__:main'],
        'console_scripts': ['mqttk-console=mqttk.__main__:main']
    },
    package_data={
        'mqttk': ['*.png']
    },
    download_url="{}/tarball/{}".format(url, __version__),
    license="LGPLv3"#,
    # **extra_options
)
