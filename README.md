![MQTTk](/mqttk/mqttk_splash.png)

# Introduction
MQTTk is a lightweight MQTT GUI client that looks dated and retarded, but it worksm or at least I think. 
It intends to replicate most features and functionality of MQTT.fx which is no longer free 
and the free version is no longer maintained. Since upgrading my computer, it was crashing 
every 2 minutes, practically becoming useless. I always found it more useful than other 
MQTT GUI clients, which mostly update the values of topics as they come in, in my work, 
being able to track message exchange over time is equally as important as the content of 
the messages themselves.

Since there is no other similar tool out there I decided to make my own and share it with
whoever is interested. The project is written in tk/ttk, I don't have time to learn some
fancy-pancy GUI environment, it was quick and easy to knock out, and it should run on anything
including the kitchen sink.

# Dependencies
The project is written in pure python, it requires python3, tk/ttk and the paho-mqtt python
package from pypi which is installed as a dependency when installed using pip, or wrapped
in the app packages (windows/mac/linux). That't it, nothing fancy.

# Installation
## On MacOS as an app
Download the latest release from the [GitHub repository](https://github.com/matesh/mqttk/releases)
and install like any other apps. MacOS might complain about being unable to identify the
developer, but [here](https://mateszabo.com) I am, so you can instead. In such case, just
Ctrl+click on the file and then "Open" in the appearing window.

## On MacOS from pypi
TBC

## On MacOS from source
### Dependencies
You must have python3 and python3-pip installed. On some versions of MacOS or the python3
package, tk/ttk is not included, in which case the python3-tk package is also needed.

The easiest way to install these, is to use brew. The commands below may be different on your
system.

```shell
$ brew install python python-tk
```
### Acquiring and installing the package
After that, download the [latest tar.gz release](insertlinkhere) from the [GitHub repository](https://github.com/matesh/mqttk/releases)
and then install it using pip.
```shell
$ pip3 install mqttk-x.y.tar.gz
```

To run the software, just issue the mqttk command. 
```shell
$ mqttk
```

If the app fails to start, you can try re-launching it using the
```shell
$ mqttk-console
```
command, which might provide additional debug information.

## On windows as an executable
Download the latest release from the [GitHub repository](https://github.com/matesh/mqttk/releases)
and install like any other apps.

## On windows from source
Download python3 from the [official website](https://www.python.org/downloads/) and install it like any other apps.

Download the [latest tar.gz release](insertlinkhere) from the [GitHub repository](https://github.com/matesh/mqttk/releases)
and then install it using pip.

```shell
> pip3 install mqttk-x.y.tar.gz
```

## On windows from pypi
TBC

## On Linux as an app
TBC

## On Linux from pypi
TBC

## On Linux from source

### Dependencies
You need to install python3, python3-pip and in some cases the python3-tk packages. The process
will be different depending on your distribution, refer to your distributions package manager or
community. As an example, on ubuntu you'd need to install the following packages using apt. On
other distros, python3 might be default, in which case the "3" suffix won't be needed on the packages.
I know, confusing times, ain't it?

```shell
$ sudo apt install python3 python3-pip python3-tk
```

# Using the app
## Main features
Currently the app allows to configure multiple connection profiles. Once configured, the brokers
can be connected to and you can subscribe to topics. Incoming messages are shown in time, their colour
can be changed and selected messages payloads displayed. There are currently 3 decoders, plain text, json
pretty formatter and hex decoder to analyse message data. 

You can also publish, save message templates and one-click publish them. You can send messages with
any QoS and retained as well. 

There is a built-in log feature to show any exceptions/debug information, let me know if you see something
unusual there.

##Planned features
- import MQTT.fx configuration file with all the subscription and publish histories, connections and whatnot
- tree-style topic inspector where all incoming messages are organised in a tree and the latest content of each will be shown
- import and export of subscribe, publish templates/history, etc.
- message dump

# Building the app from source

## pypi package
issue the following command in the project root to build the sdist package.
```shell
$ python3 setup.py sdist
```
The built package will appear in the dist/ directory.

## MacOS appimage
### Dependencies
You need to have xcode installed. Use the app store to do that if you don't have it yet.
You will also need the xcode command line tools to be installed. You can do that from the terminal:

```shell
$ xcode-select —install
```

Just like when running the app, you need python3, pip and python3-tk. Install these as explained above.

In addition, you need the py2app package. Install it using pip:
```shell
$pip install py2app
```

### Building the app
Navigate to the project root directory and issue
```shell
$  python3 setup.py py2app
```

### Windows executable
Just like when running the app, you need python3, pip and python3-tk. Install these as explained above.
In addition, you need the pyinstaller package:
```shell
> pip install pyinstaller
```

Navigate to the project root and issue the following command:
```shell
> pyinstaller mqttk_entry.py -F --collect-all mqttk --noconsole --icon=mqttk.ico
```
