# Setup Instructions

## Hardware

To setup the hardware, you'll need to hook up 4 switches and a piezo buzzer. The
first 3 switches correspond to the 3 buttons used for the code entry. These
buttons are hooked up as follows:

```
Button 1: GPIO pin 23
Button 2: GPIO pin 24
Button 3: GPIO pin 22
```

The fourth button simulates picking up/setting down the gun on the stand. This
button should be hooked up to GPIO 21. 

The piezo buzzer gives immediate feedback when either the passcode has been
incorrectly entered some number of times, or if the gun has been removed without
entering the passcode. The buzzer should be hooked up the GPIO 18.

## Software

The software setup is simple. Log onto the Raspberry Pi and open up a terminal.
Run the following command (Pi must be connected to the internet):

```
git clone https://github.com/jprestwo/james-bryan-repo.git
```

This will pull down the code that is used to run the hardware above. There is
a configuration file, example.conf, that can be used to configure certain
parameters like the notifier email, number of incorrect passcode attempts etc.

## Running the code

Use this command to run the code:

```
python main.py example.conf
```

Once it has been started you can start entering passcodes, simulate pulling the
gun off the stand etc.

