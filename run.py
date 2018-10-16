#!/usr/bin/python

#  Follow the directions to install the Adafruit DHT library
# http://www.circuitbasics.com/how-to-set-up-the-dht11-humidity-sensor-on-the-raspberry-pi/
# sudo pip install RPLCD


from datetime import datetime, timedelta
import sys
import time
import Adafruit_DHT
import RPi.GPIO as GPIO
tz = 'US/Mountain'

GPIO.setmode(GPIO.BCM) 
GPIO.setwarnings(False)
VENT_PIN = 17
HEAT_PIN = 27
GPIO.setup(VENT_PIN, GPIO.OUT)
GPIO.setup(HEAT_PIN, GPIO.OUT)

######### Global Settings ###############
# Temperature needs to be around 75 degF, set to 72 because of sensor location
SETPOINT = (75 - 32) * 5/9  #22 deg C  
DEADBAND = 2 * 5/9  # 2 deg F deadband
VENTILATION_SETPOINT = (80 - 32) * 5/9
MIN_CYCLE_TIME = 300 # seconds
SAMPLE_TIME = 60 # seconds

#########################################


def turn_off(io_port, time_since_last_cycle=MIN_CYCLE_TIME):
	"""1 is off"""
	if GPIO.input(io_port) == 1:
		# State has not changed
		return False
	else:
		if time_since_last_cycle >= MIN_CYCLE_TIME:
			GPIO.output(io_port, 1)
			return True
		else:
			# print("Changing state violates MIN_CYCLE_TIME (%s)... waiting" % time_since_last_cycle)
			return False

def turn_on(io_port, time_since_last_cycle=MIN_CYCLE_TIME):
	"""0 is on"""
	if GPIO.input(io_port) == 0:
		# State has not changed
		return False
	else:
		if time_since_last_cycle >= MIN_CYCLE_TIME:
			GPIO.output(io_port, 0)
			return True
		else:
			# print("Changing state violates MIN_CYCLE_TIME (%s)... waiting" % time_since_last_cycle)
			return False
	
def ventilation(enable, time_since_last_cycle):
	# Run ventilation for 15 minutes each hour, or when it is in hi temp mode
	# Deal with timezones by just adding 7 for now.
	if 0 <= datetime.now().minute <= 15 and 7 <= datetime.now().hour - 7 <= 20:
		# turn on ventilation
		print "Running scheduled ventilation %s" % (datetime.now().hour - 7)
		return turn_on(VENT_PIN)
	else:
		# if requesting on, then turn on, else turn off
		if enable:
			return turn_on(VENT_PIN, time_since_last_cycle)
		else:
			return turn_off(VENT_PIN, time_since_last_cycle)

# initialize 
turn_off(HEAT_PIN)
turn_off(VENT_PIN)
turn_on_ventilation = False
heater_cycle_time = 0
ventilation_cycle_time = False

with open('data.csv', 'a') as f:
	while True:
		# 11 = DHT11; 4 = GPIO 4
		humidity, temperature = Adafruit_DHT.read_retry(11, 4)

		if humidity is not None and temperature is not None:
	  		print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))

	  		if temperature > (SETPOINT + DEADBAND):
				# print "high temp - Turning off heater"
				if turn_off(HEAT_PIN, heater_cycle_time):
					heater_cycle_time = 0
				
				
			elif temperature < (SETPOINT - DEADBAND):
				# print "low temp - Turning on Heater"
				if turn_on(HEAT_PIN):
					heater_cycle_time = 0
				
				turn_on_ventilation = False
			else:
				print "within range - not changing anything"

			# Call ventilation separate so that can run independent of the temperature
			if temperature > (VENTILATION_SETPOINT + DEADBAND):
				if ventilation(True, ventilation_cycle_time):
					ventilation_cycle_time = 0
			elif temperature < (VENTILATION_SETPOINT - DEADBAND):
				if ventilation(False, ventilation_cycle_time):
					ventilation_cycle_time = 0			

			# Read the current state and save some data to CSV
			f.write("%s,%s,%s,%s,%s,%s,%s\n" % (
				datetime.now() - timedelta(hours=7),
				temperature,
				humidity,
				GPIO.input(HEAT_PIN) == 0, 
				GPIO.input(VENT_PIN) == 0,
				heater_cycle_time,
				ventilation_cycle_time
				)
			)
			f.flush()
		else:
	  		print('Failed to get reading. Try again!')

		# wait before sampling again, set cycle times
		ventilation_cycle_time += SAMPLE_TIME
		heater_cycle_time += SAMPLE_TIME

		
		time.sleep(SAMPLE_TIME)
