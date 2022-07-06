import sys, time
import math
import Adafruit_DHT as AdaDHT
from Adafruit_IO import Client, Feed
import gpiozero
from gpiozero import Button, Buzzer
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
from mq import *

#adafruit stuff
ADAFRUIT_IO_USERNAME = 'nickpop'
ADAFRUIT_IO_KEY = 'aio_VjUx49tj8sLT41XmeH6jwqPc6vQC'

aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

temperature_feed = aio.feeds('temperature')
humidity_feed = aio.feeds('humidity')
roomqualitystatus_feed = aio.feeds('roomqualitystatus')
lpg_feed = aio.feeds('lpg')
co_feed = aio.feeds('co')
smoke_feed = aio.feeds('smoke')

#define variables
dht11_sensor = AdaDHT.DHT11
DHTPin = 4
buzzerPin = 18
buttonPin = 17
relayPin = 26


#setup button and buzzer and relay
buzzer = Buzzer(buzzerPin)
button = Button(buttonPin)
#buzzer_on = False
#buzzer tone
relay = gpiozero.OutputDevice(relayPin, active_high=False, initial_value=False)

#LCD screen stuff
lcd_columns = 16
lcd_rows = 2

lcd_rs = digitalio.DigitalInOut(board.D25)
lcd_en = digitalio.DigitalInOut(board.D24)
lcd_d4 = digitalio.DigitalInOut(board.D23)
lcd_d5 = digitalio.DigitalInOut(board.D27)
lcd_d6 = digitalio.DigitalInOut(board.D21)
lcd_d7 = digitalio.DigitalInOut(board.D20)

# Initialise the lcd class
lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                          lcd_d7, lcd_columns, lcd_rows)

#-------------------------------------------------------------------------------
def playTone():
    #global buzzer_on
    def buzz(noteFreq, duration):
        halveWaveTime = 1 / (noteFreq * 2 )
        waves = int(duration * noteFreq)
        for i in range(waves):
           buzzer.on()
           time.sleep(halveWaveTime)
           buzzer.off()
           time.sleep(halveWaveTime)
    def play():
        t=0
        notes=[262,294,330,262,262,294,330,262,330,349,392,330,349,392,392,440,392,349,330,262,392,440,392,349,330,262,262,196,262,262,196,262]
        duration=[0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,1,0.5,0.5,1,0.25,0.25,0.25,0.25,0.5,0.5,0.25,0.25,0.25,0.25,0.5,0.5,0.5,0.5,1,0.5,0.5,1]
        for n in notes:
            buzz(n, duration[t])
            time.sleep(duration[t] *0.1)
            t+=1

    #buzz(262, 0.5)

    play()
    
def displayOnFirstLine(string):
    # wipe LCD screen before we start
    lcd.clear()
    lcd.cursor_position(0,0)
    lcd.message = string 

def displayOnSecondLine(string):
    lcd.cursor_position(0,1)
    lcd.message = string
    
def scroll(string):
    time.sleep(2)
    #scroll to the right
    for i in range(len(string)-16):
        lcd.move_left()
        time.sleep(1)
    #scroll to the left
    for i in range(len(string)-16):
        lcd.move_right()
        time.sleep(1)
        

def roomQualityStatus(temperature, humidity):
    roomqualitystatus = "Room Air: "
    
    if ((temperature > 26 or temperature < 18) and (humidity > 60 or humidity < 30)):
        roomqualitystatus += "Bad"
        statusBool = False
    elif (temperature > 26 or temperature < 18 or humidity > 60 or humidity < 30):
        roomqualitystatus += "Okay"
        statusBool = False
    else:
        roomqualitystatus += "Good"
        statusBool = True
    
    #roomqualitystatus = '%.2f'%(roomqualitystatus)
    #send to adafruit IO
    aio.send(roomqualitystatus_feed.key, str(roomqualitystatus))
    
    return roomqualitystatus, statusBool

def playAndTurnOffBuzzer():
    buzzer.beep()
    button.wait_for_press()
    buzzer.off()

def toggleRelay():
    relay.toggle()

def readTemperatureAndHumidity():
    humidity, temperature = AdaDHT.read_retry(dht11_sensor, DHTPin)
    #if humidity is not None and temperature is not None:
    print("Temperature={0:0.1f}*C Humidity={1:0.1f}%".format(temperature,humidity))
        # Send humidity and temperature feeds to Adafruit IO
        #temperature = '%.2f'%(temperature)
        #humidity = '%.2f'%(humidity)
        #aio.send(temperature_feed.key, str(temperature))
        #aio.send(humidity_feed.key, str(humidity))
    #else:
     #   print("Failed to retrieve data from sensor")
    return temperature, humidity

def sendTempAndHum (temperature, humidity):
    aio.send(temperature_feed.key, str(temperature))
    aio.send(humidity_feed.key, str(humidity))

def readAndSendMQ2(perc):
    lpg, co, smoke = perc["GAS_LPG"], perc["CO"], perc["SMOKE"]
    #sys.stdout.write("LPG: %g ppm" % (perc["GAS_LPG"]))
    #sys.stdout.flush()
    aio.send(lpg_feed.key, str(lpg))
    aio.send(co_feed.key, str(co))
    aio.send(smoke_feed.key, str(smoke))
    #aio.send(humidity_feed.key, str(humidity))
    #time.sleep(0.1)
    #return lpg, co, smoke


try:
    mq = MQ();
    while True:
        perc = mq.MQPercentage()
        readAndSendMQ2(perc)
        temperature, humidity = readTemperatureAndHumidity()
        sendTempAndHum(temperature, humidity)
        time.sleep(2)
        status, good = roomQualityStatus(temperature, humidity)
        displayOnFirstLine("Tp: {}C Hm: {}%".format(math.floor(temperature), math.floor(humidity)))
        displayOnSecondLine(status)
        if not good:
            relay.on()
            playAndTurnOffBuzzer()
        if good:
            relay.off()
        
        #scroll(status)
        #relay.toggle()
        time.sleep(3)

except TypeError:
    print("TypeError")
    pass

except KeyboardInterrupt:
    print("program stopped")

