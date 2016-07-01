#!/usr/bin/python

import serial
import datetime
import time
import urllib, httplib

CO2status = 1
key = 'HHQEW2LE696EWKJ6'


#function to upload data to Thingspeak
def upload(timestamp, ppm):
    while True:
	params = urllib.urlencode({'field1': ppm, 'key':key, 'created_at':timestamp, 'timezone':'Asia/Jakarta' })  
	headers = {"Content-typZZe": "application/x-www-form-urlencoded","Accept": "text/plain"}
	conn = httplib.HTTPConnection("api.thingspeak.com:80")
	try:
		conn.request("POST", "/update", params, headers)
		response = conn.getresponse()
		print ppm
		print response.status, response.reason
		data = response.read()
		conn.close()
		sent = 1
		return sent
	except:
		print "Connection Failed"
		sent = 0
		return sent
		break
	break

#check and define serial port for CO2 sensor
try:	
	port = serial.Serial('/dev/ttyUSB0',19200, timeout=3.0)
	portcheck = port.isOpen()
except serial.serialutil.SerialException, error:
	CO2status = 0
	print (error)	


#input for the sensor N = concentration in ppm;
#T = temperature in centigrade; V = lamp voltage in 10mV
if CO2status != 0:
	port.write("\rN\r")		#need to enter new line due to it 
	time.sleep(5)			#does not read first output
	ppm = port.readline()		#reading the output

	ppm = ppm.rstrip().lstrip()	#clean delimiter

#pick the timestamp when the measurement held
	timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	f = open('dataCO2.csv','a')

#writing data to file, 
#W = data written in file, not uploaded
#U = data uploaded to thingspeak
	f.write(timestamp+","+ppm+",W\n")

	f.close
else:
	print('Check sensor connection beforehand . . .')

#read and collect data from file

f = open('dataCO2.csv','rw+')
lines = f.readlines()

for i in xrange(len(lines)-1,-1,-1):	#start sorting from the latest data
	data = lines[i]
	data = data.split(",")
	timestamp = data[0]
	ppm = data[1]
	status = data[2]
	sent = 0
	if status != "U\n":
		sent = upload(timestamp, ppm)
		if sent == 1:
			lines[i]=lines[i].replace("W","U")

f.seek(0)
f.writelines(lines)
f.close



