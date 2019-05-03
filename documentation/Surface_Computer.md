# Surface Computer

In the `ssh_comm` folder of this repository, you can run the `surface_computer.py` script to connect to the robot.

## Setup

1. Connect the companion to the surface computer via ethernet.
1. Set up the surface computer to have a static IP of `192.168.2.1` (follow the Ardusub Network Setup guide [here](https://www.ardusub.com/getting-started/installation.html#raspberry-pi))
    - Note that the Pi Zero should be connected to the Pi 3 (the companion computer) via USB.
1. Follow ALL the setup instructions for the [temperature sensor](#temperature-sensor) and [pH sensor](#ph-sensor)
1. Connect the Arduino to the surface computer via USB and load the Arduino code in the `pneumatics_arduino` folder onto the arduino via the Arduino IDE.
1. Verify that the COM port used in `surface_computer.py` matches that of the Arduino.  If it does not, update it in `surface_computer.py` script
1. Everything should be setup at this point, so just run `surface_computer.py` and it should pull up a GUI (note that wherever you run the script from needs to be able to open a GUI so Windows Subsystem For Linux will not work)

## Notes

### Temperature sensor

#### Pin setup:
Red connects to 3.3V, Blue connects to ground and Yellow is data (pin 7 which is GPIO04)
4.7 kOhm resistor between data and VCC

#### Pi Setup
1. Open `/boot/config.txt` on the companion computer and add `dtoverlay=w1-gpio` to the bottom of the file (if not already there) and reboot the pi
    - Note that the `/boot/config.txt` can be accessed on the boot directory of the SD card instead of logging into the companion computer
1. Copy the `temp_reading.py` script to the companion computer in its home directory

### pH Sensor
Not finished - latest untested code on jcassarly/ph branch
