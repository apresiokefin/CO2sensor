#!/usr/bin/python

import serial
import datetime
import time

CO2status = 1
SIMstatus = 1
key = 'HHQEW2LE696EWKJ6'

#List ATcommand used for the process
atcmd = 	("AT\r",\
		"AT+COPS?\r",\
		"AT+CREG?\r",\
		"AT+CSQ\r",\
		"AT+SAPBR=3,1,\"CONTYPE\",\"GPRS\"\r",\
		"AT+SAPBR=3,1,\"APN\",\"indosatgprs\"\r",\
		"AT+SAPBR=1,1\r",\
		"AT+SAPBR=2,1\r",\
		"AT+SAPBR=0,1\r",\
		"AT+HTTPINIT\r",\
		"AT+HTTPPARA=\"CID\",1\r",\
		"AT+HTTPACTION=0\r",\
		"AT+HTTPREAD\r",\
		"AT+HTTPTERM\r",\
		"AT+CCLK?\r")

#ATcommand send and read through serial port, refer to ATcommand list
def sdatcmd(val): 
	simport.write(atcmd[val])
	time.sleep(8)
	response = rdln(simport)
	print(response)
	return response

#send and read serial port command
def sdcmd(val): 
	simport.write(val)
	time.sleep(8)
	response = rdln(simport)
	print(response)
	return response

#readline function for SIM800L serial
def rdln(simport):
        ro = ""
        while True:
                rn = simport.read()
                ro += rn
                if rn=='':
                        return ro

#GPRS initialization
def initgprs():
	sdatcmd(0) #AT
	sdatcmd(4) #AT+SAPBR=3,1
	sdatcmd(5)
	response = sdatcmd(6) #AT+SAPBR=1,1
	if response.find("ERROR") >= 0:
		sdatcmd(8) #deactivating bearer
		response = sdatcmd(6) #reactivating bearer
		if response.find("ERROR") >= 0:
			SIMstatus = 0
			return SIMstatus
			print ("Bearer activation problem: unsolved!")

	response = sdatcmd(7) #AT+SAPBR=2,1
	if response.find("0.0.0.0") >= 0:
		SIMstatus = 0
		return SIMstatus
		print ("IP address not initialized!")
	
	response = sdatcmd(9) #AT+HTTPINIT
	if response.find("ERROR") >= 0:
		sdatcmd(13) #AT+HTTPTERM
		response = sdatcmd(9) #AT+HTTPINIT
		if response.find("ERROR") >= 0:
			SIMstatus = 0
			return SIMstatus
			print ("Initializing HTTP Service failed!")
	response = sdatcmd(10) #AT+HTTPPARA="CID",1
	if response.find("ERROR") >= 0:
		response = sdatcmd(10) #repeating input
		if response.find("ERROR") >= 0:
			SIMstatus = 0
			return SIMstatus
			print ("Identifying bearer profile failed!")
#terminating GPRS connection
def termgprs():
	sdatcmd(13) #AT+HTTPTERM
	sdatcmd(8) #AT+SAPBR=0,1

#function to upload data to Thingspeak using Sim800L
def upload(timestamp, ppm):
    while True:
	
	try: 
		cmdupload="AT+HTTPPARA=\"URL\",\"http://api.thingspeak.com/update?api_key="+key+"&field1="+ppm+"&created_at="+timestamp+"&timezone=Asia/Jakarta\"\r"
		response = sdcmd(cmdupload)
		if response.find("ERROR") >= 0:
			print ("Upload failed!")
		response = sdatcmd(11) #AT+HTTPACTION=0
		if response.find("200") >= 0: #OK
			print (ppm)
			print (timestamp)
			print ("OK")
			sent = 1
		return sent
	except:
		print "HTTP Connection failed"
		termgprs()
		sent = 0
		return sent
		break
	break

#check and define serial port for SIM800L
if True:
	try:	
		simport = serial.Serial('/dev/ttyATH0',9600, timeout=3.0)
		simportcheck = simport.isOpen()
	except (serial.serialutil.SerialException,OSError), error:
		SIMstatus = 0
		print (error)

#check and define serial port for CO2 sensor
if True:
	try:	
		port = serial.Serial('/dev/ttyUSB0',19200, timeout=3.0)
		portcheck = port.isOpen()
	except (serial.serialutil.SerialException,OSError), error:
		CO2status = 0
		print (error)	

#input for the sensor N = concentration in ppm;
#T = temperature in centigrade; V = lamp voltage in 10mV
#begin sampling data from CO2 sensor
if CO2status != 0:
	port.write("\rN\r")		#need to enter new line due to it . . .
	time.sleep(5)			# . . .does not read the first output
	ppm = port.readline()		#reading the output

	ppm = ppm.rstrip().lstrip()	#clean delimiter

#pick the timestamp when the measurement held
	timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

	f = open('dataCO2.csv','a')

#writing data to file, 
#W = data written in file, not uploaded
#U = data uploaded to thingspeak
	f.write(timestamp+","+ppm+",W\n")

	f.close
else:
	print('Check sensor connection beforehand . . .')

#begin uploading procedure
if SIMstatus != 0:
	SIMstatus = initgprs()
else:
	print ("Check SIM800 serial connection")

#read and collect data from file
if SIMstatus != 0:
	f = file('dataCO2.csv','r+b')
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
			else:
				break

	f.seek(0)
	f.writelines(lines)
	f.close
	termgprs()
else:
	print ("GPRS Connection Initialization Failed")
