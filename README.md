# Setup Instructions

## Hardware

To setup the hardware, you'll need to hook up 4 switches and a piezo buzzer. The
first 3 switches correspond to the 3 buttons used for the code entry. These
buttons are hooked up as follows:

```
Button 1: GPIO pin 23
Button 2: GPIO pin 24
Button 3: GPIO pin 22
Gun Trigger: GPIO pin 27
Piezo Buzzer: GPIO 18
```

The Gun Trigger button simulates picking up/setting down the gun on the stand. For simplicity,
this button is configured to change the state every time you press it, rather than
maintaining the actual state of the button (as if the weight of the gun was holding it down).
For example, the intial state assumes the gun is on the stand; pressing the button will
simulate removing the gun, and pressing it again will simulate putting the gun back on
the stand. 

The piezo buzzer gives immediate feedback when either the passcode has been
incorrectly entered some number of times, or if the gun has been removed without
entering the passcode.

## Software

The software setup is simple. Log onto the Raspberry Pi and open up a terminal.
Run the following command (Pi must be connected to the internet):

```
git clone https://github.com/jprestwo/james-bryan-repo.git
```

This will pull down the code that is used to run the hardware above. There is
a configuration file, example.conf, that can be used to configure certain
parameters like the notifier email, number of incorrect passcode attempts etc.

## Configuration file

When running, a configuration file should be supplied. This file should contain information
such as the SMTP email server, the notifier email address, email message etc. There is an
example configuration file, example.conf that can be used as default.

## Running the code

Use this command to run the code:

```
python main.py example.conf
```

Once it has been started you can start entering passcodes, simulate pulling the
gun off the stand etc.

The logic is as follows:

Entering the passcode will lock/unlock the system. If the gun is not on the stand, locking
the system will have no effect. If the gun is on the stand, entering the passcode will
lock the system, where if the gun is removed, the buzzer will sound and an email notification
will be sent to the email address in the config file. If the system is locked and the correct
passcode is entered, the gun can be freely removed and placed any number of times until the
system is locked again.

