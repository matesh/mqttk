![MQTTk](/mqttk/mqttk_splash.png)

- [Introduction](#introduction)
- [Software dependencies](#software-dependencies)
- [Installation](#installation)
- [macOS - as an app - M1 (ARM64) macs only!](#macos---app)
  * [On macOS from source](#on-macos-from-source)
    + [macOS Dependencies](#macos-dependencies)
    + [macOS - acquiring and installing the package from source](#macos---acquiring-and-installing-the-package-from-source)
    + [macOS - installing via pip](#macos---installing-via-pip)
    + [macOS - running MQTTk](#macos---running-mqttk)
  * [Windows - as an executable](#windows---as-an-executable)
  * [Windows - from source](#windows---from-source)
    + [Windows - dependencies](#windows---dependencies)
    + [Windows - acquiring and installing the package from source](#windows---acquiring-and-installing-the-package-from-source)
    + [Windows - installing it via pip](#windows---installing-it-via-pip)
    + [Windows - running MQTTk](#windows---running-mqttk)
  * [On Linux from source](#on-linux-from-source)
    + [Linux - dependencies](#linux---dependencies)
    + [Linux - acquiring and installing the package from source](#linux---acquiring-and-installing-the-package-from-source)
    + [Linux - installing it via pip](#linux---installing-it-via-pip)
    + [Linux - Running MQTTk](#linux---running-mqttk)
- [Using the app](#using-the-app)
  * [Features](#features)
  * [Planned features](#planned-features)
    + [V1.1](#v11)
    + [V1.2](#v12)
    + [V1.3](#v13)
- [Building the app from source](#building-the-app-from-source)
  * [pypi package](#pypi-package)
  * [macOS appimage](#macos-appimage)
    + [Dependencies](#dependencies)
    + [Building the macOS app](#building-the-macos-app)
  * [Windows executable](#windows-executable)
- [How to contribute](#how-to-contribute)
  * [Reporting bugs](#reporting-bugs)
  * [macOS universal2 appimage](#macos-universal2-appimage)
  * [Linux binary package or app](#linux-binary-package-or-app)

# Introduction
MQTTk is a very lightweight MQTT GUI client that looks retarded, but it does the job fast in a native
fashion, without bloated and sluggish browser, java and javascript based rubbish that may look good, but
are a pain to use especially in a professional environment.

It intends to replicate most features and functionality of MQTT.fx which is no longer free 
and the free version is no longer maintained. Since upgrading my computer, it was crashing 
every minute, practically becoming useless. I always found it more useful than other 
MQTT GUI clients, which mostly update the values of topics as they come in, in my work, 
being able to track message exchange over time is as important as the content of 
the messages themselves.

Since there is no other similar tool out there, I decided to make my own and share it with
whoever is interested. The project is written in Tk/ttk. I don't have time to learn some
fancy-pancy GUI environment, it was quick and easy to knock out, and it should run on anything
including the kitchen sink without too much pain.

# Software dependencies
The project is written in pure python, powered by the below projects: 
- [python3.7+](https://www.python.org/)
- [Tkinter/ttk](https://docs.python.org/3/library/tkinter.html) 
- [Eclipse paho-mqtt python client](https://github.com/eclipse/paho.mqtt.python)
- [xmltodict](https://github.com/martinblech/xmltodict) 
That't it, nothing fancy. Give the above projects a big thumbs up!

# Installation
# macOS - app
:warning: The built appimage is experimental! Use it at your own risk, it may cause kernel panics and app crashes.

:warning: The app image is only for M1 (ARM64, Apple Silicon) macs! With my current knowledge I can't produce a working
intel or universal2 app image.

Download the latest release from [the GitHub releases page](https://github.com/matesh/mqttk/releases) and install it
like any other apps. 

The system may complain about not being able to verify the developer. You can find more information
about me [here](https://mateszabo.com), so you can verify the developer yourself instead. To run the app, follow
the instructions provided by apple [here](https://support.apple.com/en-ie/guide/mac-help/mh40616/mac).

## On macOS from source
### macOS Dependencies
You must have Python 3.7+ and pip installed. On some versions of macOS or the python package, Tk/ttk is not included, 
in which case the python-tk package is also needed. 

The easiest way to install these, is to use [homebrew](https://brew.sh/). 
The commands below may be different on your system. Open the terminal and issue these commands:

```shell
$ brew install python python-tk
```

:warning: When installing/running the app, use the system interpreter, or the interpreter available via homebrew.
During my testing, Conda or other interpreters occasionally caused my system to crash entirely (kernel panic) and
when using mission control to switch between apps, MQTTk crashed regularly.
The cause is outside the code of this software. This crash happens under certain circumstances when switching
to the app via mission control or the dock, there's nothing I can do about it, unfortunately. Therefore,
use other interpreters at your own risk!

### macOS - acquiring and installing the package from source
Download the latest release from the [GitHub repository](https://github.com/matesh/mqttk/releases)
and install it using pip.
```shell
$ pip3 install mqttk-x.y.tar.gz
```

### macOS - installing via pip
Issue the following command:
```shell
$ pip3 install mqttk
```

### macOS - running MQTTk
To run the software, just issue the mqttk command from the terminal. 
```shell
$ mqttk
```

If the app fails to start, or crashes randomly, try re-launching it using the
```shell
$ mqttk-console
```
command. This will leave a console window, which might provide additional debug information when something goes tits up.

## Windows - as an executable
Download the latest release from the [GitHub repository](https://github.com/matesh/mqttk/releases)
and install/run like any other apps.

## Windows - from source
### Windows - dependencies
Download python3 from the [official website](https://www.python.org/downloads/) and install it like any other apps.

### Windows - acquiring and installing the package from source
Download the latest release from the [GitHub repository](https://github.com/matesh/mqttk/releases)
and then install it using pip and the command line:

```shell
> pip3 install mqttk-x.y.tar.gz
```

### Windows - installing it via pip
Issue the following command in the command line:
```shell
> pip3 install mqttk
```

### Windows - running MQTTk
In the command line issue the command:
```shell
> mqttk
```

If the app fails to start, or crashes randomly, try re-launching it using the
```shell
$ mqttk-console
```
command. This will leave a console window, which might provide additional debug information when something goes tits up.


## On Linux from source
### Linux - dependencies
You need to install python3, python3-pip and in some cases the python3-tk packages. The process
will be different depending on your distribution, refer to your distributions package manager or
community. As an example, on ubuntu you'd need to install the below packages using apt. On
other distros, python3 might be default, in which case the "3" suffix won't be needed on the packages.

```shell
$ sudo apt install python3 python3-pip python3-tk
```

### Linux - acquiring and installing the package from source
Download the latest release from the [GitHub repository](https://github.com/matesh/mqttk/releases)
and install it using pip.
```shell
$ pip3 install mqttk-x.y.tar.gz
```

### Linux - installing it via pip
Just issue the command
```shell
$ pip3 install mqttk
```

### Linux - Running MQTTk

From the command line issue the command
```shell
$ mqttk
```

If the app fails to start, or crashes randomly, try re-launching it using the
```shell
$ mqttk-console
```
command. This will leave a console window, which might provide additional debug information when something goes tits up.

# Using the app
## Features
MQTTk allows configuration of multiple connection profiles. Once configured, the brokers
can be connected to, and you can subscribe to topics. Incoming messages are shown in time, their colour
can be changed and selected message's payloads displayed. There are currently 3 decoders, plain text, json
pretty formatter and hex decoder to analyse message data. 

You can also publish messages, save message templates and one-click publish them. You can send messages with
any QoS and retained messages as well.

So far, I added the most useful message decoding features: JSON pretty formatter and hex decoders. 

If you used MQTT.fx in the past, MQTTk will try to find and import your config. The connection profiles,
subscribe and publish history will be imported, as well as the saved message templates.

There is a built-in log feature to show any exceptions/debug information, let me know if you see something
unusual there.

## Planned features
### V1.1
- Export and import MQTTk configuration
- Export and import subscribe topic history, publish topic history and templates
- Message dump
- Log output to file and better logging

### V1.2
- tree-style topic inspector where all incoming messages are organised in a tree and the latest payload is shown

### V1.3
- Broker stats tab

# Building the app from source
## pypi package
issue the following command in the project root to build the sdist package.
```shell
$ python3 setup.py sdist
```
The built package will appear in the dist/ directory.

## macOS appimage
:warning: This is highly experimental and needs refiniement!

:warning: When building the app, use the system interpreter, or the interpreter available via homebrew.

Conda or other interpreters can cause your system to crash entirely (kernel panic) which issue is
outside of the code of this software. This crash happens under certain circumstances when switching
to the app via mission control or the dock. Use other interpreters at your own risk!

### Dependencies
You need to have xcode installed. Use the app store to do that if you don't have it yet.
You will also need the xcode command line tools to be installed. You can do that from the terminal:

```shell
$ xcode-select —install
```

Just like when running the app, you need python3, pip and python3-tk. Install these as explained above.

In addition, you need the pyinstaller package. Install it using pip:

```shell
$ pip install pyinstaller
```

### Building the macOS app
I was not able to build a universal app image for MACs that ran native on both Intel and M1 architectures,
so I only built the ARM64 package.

Navigate to the project root and issue

```shell
$  pyinstaller mqttk.spec
```

## Windows executable
Just like when running the app, you need python3, pip and python3-tk. Install these as explained above.
In addition, you need the pyinstaller package, use the command line:

```shell
> pip3 install pyinstaller
```

Navigate to the project root and issue the following command:
```shell
> pyinstaller mqttk.spec
```

# How to contribute
## Reporting bugs
Use the GitHub [issue reporting page](https://github.com/matesh/mqttk/issues) of the project to help me squish bugs.

## macOS universal2 appimage
My time and knowledge is limited to figure how to properly build a universal2 app image (intel + ARM). I managed to
build an M1 only version, with which I'm not entirely happy, it takes a long time to start up for some reason. Furthermore,
I had issues with the app when not running on the system interpreter on my M1 mac, causing regular crashes and
kernel panics when switching to and from MQTTk. I would appreciate help with building the app and testing the 
resulting image out on other machines. 

## Linux binary package or app
There are more ways to distribute apps on various linux distros than stars on the sky. I'd appreciate recommendations
on what format to use and maybe a helping hand figuring it out and getting things set up.