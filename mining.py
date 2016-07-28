#!/usr/bin/python

import serial
import datetime
import time
import os

PMstatus = 1
CO2status = 1
ttyPM = '/dev/ttyUSB0'
ttyCO2 = '/dev/ttyUSB1'

#readline function to read from serial
def rdln(port):
        ro = ""
        while True:
                rn = port.read()
                ro += rn
                if rn=='':
                        return ro

#check wheter output of the sensor is float
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

#dictionary to convert month's name to number
def month(x):
	return {
		'JAN': '01',
		'FEB': '02',
		'MAR': '03',
		'APR': '04',
		'MAY': '05',
		'JUN': '06',
		'JUL': '07',
		'AUG': '08',
		'SEP': '09',
		'OCT': '10',
		'NOV': '11',
		'DEC': '12',
	} [x]

#check and define serial port for particulate sensor
try:	
	PMport = serial.Serial(ttyPM,38400, timeout=3.0)
	PMportcheck = PMport.isOpen()
	PMstatus = 1
except (serial.serialutil.SerialException,OSError), error:
	PMstatus = 0
	print (error)

#check and define serial port for CO2 sensor
try:	
	CO2port = serial.Serial(ttyCO2,19200, timeout=3.0)
	CO2portcheck = CO2port.isOpen()
	CO2status = 1
except (serial.serialutil.SerialException,OSError), error:
	CO2status = 0
	print (error)

if PMstatus != 0:
	PMport.write("S\r")
	time.sleep(5)
	response=rdln(PMport)
	if response.find("Start") >= 0:
		time.sleep(75)		
		data = PMport.readline()	#reading the output
		data = data.lstrip().rstrip()	#clean delimiter
		data = data.split(",")
		timestamp = data[0].split(" ")
		date = timestamp[0].split("/")
		hms = timestamp[1] #hms = hour-minute-second
		
		dd = date[0]
		mm = month(date[1])
		yyyy = date[2]
		timestamp = yyyy+"-"+mm+"-"+dd+"T"+hms 
		ppm = 0
		if CO2status != 0:
			while True:			
				CO2port.write("N\r")	
				ppm = CO2port.readline()
				ppm = ppm.rstrip().lstrip()	
				if is_number(ppm) == True:
					break
		else:
			print('CO2 sensor problem connection . . .')
		f = file('datasensync.csv','a',os.O_NONBLOCK)
		f.write(timestamp+","+data[2]+","+data[3]+","+data[4]+","+data[5]+","+data[6]+","+ppm+",W\n")

		f.close
	else:
		print('Sensor does not start . . .')
else:
	print('PM sensor problem connection . . .')
