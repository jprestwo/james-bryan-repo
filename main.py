import RPi.GPIO as GPIO
import time
import smtplib
import sys

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
GMAIL_USERNAME = 'gun.stand.notification@gmail.com'
GMAIL_PASSWORD = 'gunstand'

BUTTON_1_PIN = 23
BUTTON_2_PIN = 24
BUTTON_3_PIN = 22
BUTTON_GUN_PIN = 27

modifier_map = [None]*30
modifier_map[BUTTON_1_PIN] = 1
modifier_map[BUTTON_2_PIN] = 2
modifier_map[BUTTON_3_PIN] = 3

modifier = 100
current_code = 0
current_idx = 1
correct_code = 111
incorrect_count = 0
gunState = 'on'
state = 'locked'

cfg_email = 'prestwoj@gmail.com'
cfg_subject = 'Gun Stand Notification'
cfg_invalid_entry = 5
cfg_invalid_entry_message = 'Incorrect passcode has been entered 5 times'

done = False

GPIO.setmode(GPIO.BCM)

GPIO.setup(BUTTON_1_PIN, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

GPIO.setup(BUTTON_2_PIN, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

GPIO.setup(BUTTON_3_PIN, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

GPIO.setup(BUTTON_GUN_PIN, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

GPIO.setup(18, GPIO.OUT)

def readConfig(file):
    config = []
    line = 1
    with open(file) as f:
        content = [x.strip('\n') for x in f.readlines()]

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
                config.append(s)
            line += 1

    return config

def sendNotification(email, message):
    recipient = email
    subject = cfg_subject
    emailText = message

    emailText = "" + emailText + ""

    headers = ["From: " + GMAIL_USERNAME,
               "Subject: " + subject,
               "To: " + recipient,
               "MIME-Version: 1.0",
               "Content-Type: text/html"]
    headers = "\r\n".join(headers)

    session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

    session.ehlo()
    session.starttls()
    session.ehlo

    session.login(GMAIL_USERNAME, GMAIL_PASSWORD)

    session.sendmail(GMAIL_USERNAME, recipient, headers + "\r\n\r\n" + emailText)
    session.quit()

def playPass():
    count = 0
    while count < 3:
        inner = 0
        while inner < 20:
           GPIO.output(18, True)
           time.sleep(0.001)
           GPIO.output(18, False)
           time.sleep(0.001)
           inner += 1

        time.sleep(0.1)
        count += 1

def playError():
    count = 0
    while count < 40:
        GPIO.output(18, True)
        time.sleep(0.01)
        GPIO.output(18, False)
        time.sleep(0.01)
        count += 1

def reset():
    global current_code
    global modifier
    global current_idx
    global correct_code
    global incorrect_count
    global cfg_invalid_entry
    global cfg_email
    global state

    print("Reset!")
    print("Code entered = " + str(current_code))
    if current_code != correct_code:
        playError()
        incorrect_count += 1
        if int(incorrect_count) >= int(cfg_invalid_entry):
            print "Incorrect code entered 5 times, sending email notification"
            sendNotification(cfg_email, cfg_invalid_entry_message)
            incorrect_count = 0
    else:
        playPass()
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

def gunTriggered(channel):
    global gunState
    global state

    if gunState == 'on':
        print "Gun removed"
        if state == 'locked':
            playError()
            sendNotification(cfg_email, "The gun was removed without passcode")
        else:
            print "Gun was removed correctly"
        gunState = 'off'
    elif gunState == 'off':
        print "Gun placed"
        gunState = 'on'

# Add up the code presses to form the final code entry after 3 presses
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

config = readConfig(sys.argv[1])

for i in config:
    if i[0] == 'EmailUser':
        GMAIL_USERNAME = i[1]
    elif i[0] == 'EmailPass':
        GMAIL_PASSWORD = i[1]
    elif i[0] == 'SMTPServer':
        SMTP_SERVER = i[1]
    elif i[0] == 'SMTPPort':
        SMTP_PORT = i[1]
    elif i[0] == 'NotifierEmail':
        cfg_email = i[1]
    elif i[0] == 'EmailSubject':
        cfg_subject = i[1]
    elif i[0] == 'InvalidEntryLimit':
        cfg_invalid_entry = i[1]
    elif i[0] == 'InvalidEntryMessage':
        cfg_invalid_entry_message = i[1]

GPIO.add_event_detect(BUTTON_1_PIN, GPIO.RISING, callback=buttonCallback, bouncetime=300)
GPIO.add_event_detect(BUTTON_2_PIN, GPIO.RISING, callback=buttonCallback, bouncetime=300)
GPIO.add_event_detect(BUTTON_3_PIN, GPIO.RISING, callback=buttonCallback, bouncetime=300)
GPIO.add_event_detect(BUTTON_GUN_PIN, GPIO.RISING, callback=gunTriggered, bouncetime=300)

print "Initial gun state = " + gunState
print "Initial state = " + state

while True:
    if done == True:
        break

GPIO.cleanup
