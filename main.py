import RPi.GPIO as GPIO
import time
import smtplib
import sys
import thread

# Raspberry Pi button mappings
BUTTON_1_PIN = 23
BUTTON_2_PIN = 24
BUTTON_3_PIN = 22
BUTTON_GUN_PIN = 27
BUZZER_PIN = 18

MAX_GPIO_PIN = max(BUTTON_1_PIN, BUTTON_2_PIN, BUTTON_3_PIN, BUTTON_GUN_PIN)

# Maps Raspi GPIO buttons to code entry keys
modifier_map = [None]*MAX_GPIO_PIN
modifier_map[BUTTON_1_PIN] = 1
modifier_map[BUTTON_2_PIN] = 2
modifier_map[BUTTON_3_PIN] = 3

# Used to determine the weight of each button press (3 buttons = 100, 4 = 1000 etc)
modifier = 100
# Holds the current code being entered
current_code = 0
# The number of entry buttons that have been pressed
current_idx = 1
# Number of incorrect passcode tries
incorrect_count = 0
# State of the gun on the stand, on or off
gunState = 'on'
# State of the system, locked or unlocked
state = 'locked'
# Will hold the values from the config files passed in
config = {}
# This is just to keep the program running forever
done = False
# Maps carrier names to the email suffixs for texting via email
carrier_map = {
    'AT&T':'txt.att.net'  ,
    'T-Mobile':'tmomail.net',
    'Verizon':'vtext.com',
    'Sprint':'pm.sprint.com',
    'Sprint PCS':'messaging.sprintpcs.com',
    'Virgin Mobile':'vmobl.com',
    'Tracfone':'mmst5.tracfone.com',
    'Metro PCS':'mymetropcs.com',
    'Boost Mobile':'myboostmobile.com',
    'Cricket':'sms.mycricket.com',
    'Nextel':'messaging.nextel.com',
    'Alltel':'message.alltel.com',
    'Ptel':'ptel.com',
    'Suncom':'tms.suncom.com',
    'Qwest':'qwestmp.com',
    'US Cellular':'email.uscc.net'
}

# Turn a phone number and carrier into a usable email address
def makeCarrierEmail(number, carrier):
    global carrier_map
    return str(number) + '@' + carrier_map[carrier]

# Read in a config file and return the config dictionary
def readConfig(file):
    c = {}
    line = 1
    # Open the file and read in each line, also separating by '=' into list
    with open(file) as f:
        content = [x.strip('\n') for x in f.readlines()]

    # Loop through the list and parse the config
    for i in content:
        # Skip empty lines
        if len(i) > 1:
            # Skip commented lines
            if i[0] == '#':
                continue
            s = i.split('=')
            if len(s) != 2:
                print "Error on line " + str(line) + " : '" + str(i) + "'"
                exit()
            else:
                # Add each option and value to the dictionary
                c[s[0]] = s[1]
            line += 1
    # Return the dictionary
    return c

# Send an email notification
def sendNotification(email, message):
    global config

    # Setup email values
    recipient = email
    subject = config['EmailSubject']
    emailText = message

    emailText = "" + emailText + ""

    headers = ["From: " + config['EmailUser'],
               "Subject: " + subject,
               "To: " + recipient,
               "MIME-Version: 1.0",
               "Content-Type: text/html"]
    headers = "\r\n".join(headers)

    session = smtplib.SMTP(config['SMTPServer'], int(config['SMTPPort']))

    session.ehlo()
    session.starttls()
    session.ehlo

    session.login(config['EmailUser'], config['EmailPass'])

    session.sendmail(config['EmailUser'], recipient, headers + "\r\n\r\n" + emailText)
    session.quit()

# Play the success tone (3 beeps)
def playPass():
    global config
    count = 0

    while count < int(config['BeepsOnSuccess']):
        inner = 0
        while inner < int(config['SuccessBeepLength']):
            # Sofware driven PWM
            GPIO.output(18, True)
            time.sleep(0.001)
            GPIO.output(18, False)
            time.sleep(0.001)
            inner += 1

        time.sleep(0.1)
        count += 1

# Play the error tone (1 long beep)
def playError():
    global config
    count = 0

    while count < int(config['ErrorBeepLength']):
        # Software driven PWM
        GPIO.output(18, True)
        time.sleep(0.01)
        GPIO.output(18, False)
        time.sleep(0.01)
        count += 1

# Should be started in a new thread, plays pass or fail tones
def playThread(name, fail):
    if fail:
        playError()
    else:
        playPass()

# Starts a new thread to play the pass/fail tones
def playTone(fail):
    thread.start_new_thread(playThread, ("Play-Thread", fail))

# Reset the state, determines if code entry was correct and responds
def reset():
    global config
    global current_code
    global modifier
    global current_idx
    global incorrect_count
    global cfg_invalid_entry
    global cfg_email
    global state

    print("Reset!")
    print("Code entered = " + str(current_code))
    if current_code != config['Passcode']:
        playTone(False)
        incorrect_count += 1
        if incorrect_count > int(config['InvalidEntryLimit']):
            print "Incorrect code entered 5 times, sending email notification"
            if config['TextAlert'] == 'on':
                email = makeCarrierEmail(config['PhoneNumber'], config['PhoneCarrier'])
                sendNotification(email, config['InvalidEntryMessage'])
            if config['EmailAlert'] == 'on':
                sendNotification(config['NotifierEmail'], config['InvalidEntryMessage'])
            incorrect_count = 0
    else:
        playTone(True)
        incorrect_count = 0
        if state == 'unlocked':
            if gunState == 'off':
                print "Gun must be on the table before locking the system"
            else:
                print "Changing state to locked, gun is " + gunState + " the table"               
                state = 'locked'
        elif state == 'locked':
            print "Changing state to unlocked, gun is " + gunState + " the table"
            state = 'unlocked'
    current_code = 0
    modifier = 100
    current_idx = 1

# Callback for gun removal/placement
def gunTriggered(channel):
    global gunState
    global state
    global config

    if gunState == 'on':
        print "Gun removed"
        if state == 'locked':
            playTone(False)
            if config['TextAlert'] == 'on':
                email = makeCarrierEmail(config['PhoneNumber'], config['PhoneCarrier'])
                sendNotification(email, config['InvalidRemovalMessage'])
            if config['EmailAlert'] == 'on':
                sendNotification(config['NotifierEmail'], config['InvalidRemovalMessage'])
        else:
            print "Gun was removed correctly"
        gunState = 'off'
    elif gunState == 'off':
        print "Gun placed"
        gunState = 'on'

# Callback for the 3 code entry buttons
def buttonCallback(channel):
    global current_idx
    global current_code
    global modifier_map
    global modifier

    print("Button " + str(channel) + " pressed. code = " + str(modifier_map[channel]))
    print("index = " + str(current_idx) + " mod = " + str(modifier))        
    current_code += (modifier_map[channel] * modifier)
    current_idx += 1
    modifier /= 10
    if current_idx == 4:
        reset()

# Set the GPIO mode
GPIO.setmode(GPIO.BCM)

# Setup all the keypad buttons
GPIO.setup(BUTTON_1_PIN, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(BUTTON_2_PIN, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(BUTTON_3_PIN, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

# Setup the Piezo buzzer
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# Read in the configuration file (passed as the first argument)
if len(sys.argv) < 2:
    print "Usage: python main.py <config file>"
    exit()
else:
    config = readConfig(sys.argv[1])

# Add event handlers for the 4 buttons
GPIO.add_event_detect(BUTTON_1_PIN, GPIO.RISING, callback=buttonCallback, bouncetime=300)
GPIO.add_event_detect(BUTTON_2_PIN, GPIO.RISING, callback=buttonCallback, bouncetime=300)
GPIO.add_event_detect(BUTTON_3_PIN, GPIO.RISING, callback=buttonCallback, bouncetime=300)
GPIO.add_event_detect(BUTTON_GUN_PIN, GPIO.RISING, callback=gunTriggered, bouncetime=300)

print "Initial gun state = " + gunState
print "Initial state = " + state

# Run forever
while True:
    if done == True:
        break

GPIO.cleanup
