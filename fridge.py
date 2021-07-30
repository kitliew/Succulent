import glob
import time
import datetime
import RPi.GPIO as GPIO
import logging

## raspberry pi setup
GPIO.setmode(GPIO.BCM)
TEMP_GPIO = 21
GPIO.setup(TEMP_GPIO, GPIO.OUT)
GPIO_STATE = 0

## temperature reading directory
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

## Other Parameter
START_TIME = datetime.time(5,0,0)
END_TIME = datetime.time(22,59,59)
DAY_TEMP_HIGH = 26
DAY_TEMP_LOW = 25.5
NIGHT_TEMP_LOW = 17.3
NIGHT_TEMP_HIGH = 17.5

## logging info
logging.basicConfig(filename='/home/pi/Fridge/fridge.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')



def time_in_range(start, end, current):
	"""Return whether current is in range [start, end]"""
	return start <= current <= end

def read_temp_raw():
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines

def read_temp():
	lines = read_temp_raw()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
	logging.info(f"Current temperature: {temp_c}")
	return temp_c

def relay_switch_on():
	GPIO.output(TEMP_GPIO, GPIO.HIGH)
	logging.info("Relay ON")

def relay_switch_off():
	GPIO.output(TEMP_GPIO, GPIO.LOW)
	logging.info("Relay OFF")

## Run the script
logging.debug("Start script.")

# init connection to sensor
max_try = 0

try:

	logging.debug("Start loop")

	while True:
		current_time = datetime.datetime.now().time()
		print(current_time)

		try:
			current_temp = read_temp()
			print(current_temp)

		except Exception as e:
			print(e)
			max_try += 1
			logging.warning(f"Sensor fail, retry attempt: {max_try}")
			if max_try >= 3:
				GPIO.output(TEMP_GPIO, GPIO.LOW)
				logging.critical("Script will now terminate due to error")
				logging.critical(e)
				break
			time.sleep(60)

			continue

		time.sleep(60)

		if time_in_range(START_TIME,END_TIME,current_time):
			print("DAYTIME")
			logging.info("DAYTIME")
			if current_temp > DAY_TEMP_HIGH:
				relay_switch_on()
			if current_temp <= DAY_TEMP_LOW:
				relay_switch_off()

		else:
			print("NIGHTTIME")
			logging.info("NIGHTTIME")
			if current_temp > NIGHT_TEMP_HIGH:
				relay_switch_on()
			if current_temp <= NIGHT_TEMP_LOW:
				relay_switch_off()

except Exception as e:
	print(e)
	logging.error("Outside loop")
	logging.error(e)

finally:
	GPIO.output(TEMP_GPIO, GPIO.LOW)
	logging.error("INTERUPTED. SWITCH OFF RELAY NOW!")
	GPIO.cleanup()
	logging.debug("Cleanup GPIO complete.")