#!/usr/bin/python

import serial
import datetime
import time

PMstatus = 1
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
def upload(timestamp, pm1, pm25, pm4, pm10, tsp):
    while True:
	
	try: 
		cmdupload="AT+HTTPPARA=\"URL\",\"http://api.thingspeak.com/update?api_key="+key+"&field2="+pm1+"&field3="+pm25+"&field4="+pm4+"&field5="+pm10+"&field6="+tsp+"&created_at="+timestamp+"&timezone=Asia/Jakarta\"\r"
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
		sent = 0
		return sent
		break
	break

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

#check and define serial port for SIM800L
try:	
	simport = serial.Serial('/dev/ttyATH0',9600, timeout=3.0)
	simportcheck = simport.isOpen()
except (serial.serialutil.SerialException,OSError), error:
	SIMstatus = 0
	print (error)

#check and define serial port for particulate sensor
try:	
	port = serial.Serial('/dev/ttyUSB0',38400, timeout=3.0)
	portcheck = port.isOpen()
except (serial.serialutil.SerialException,OSError), error:
	PMstatus = 0
	print (error)	

#input for the sensor S = start sampling data;
#begin sampling data from particulate sensor
if PMstatus != 0:
	port.write("\r")
	time.sleep(5)
	port.write("S\r")
	time.sleep(5)
	response=rdln(port)
	if response.find("Start") >= 0:
		time.sleep(65)		
		data = port.readline()		#reading the output
	data = data.lstrip().rstrip()	#clean delimiter
	data = data.split(",")
	timestamp = data[0].split(" ")
	date = timestamp[0].split("/")
	time = timestamp[1]

	dd = date[0]
	mm = month(date[1])
	yyyy = date[2]
	timestamp = yyyy+"-"+mm+"-"+dd+"T"+time

	f = open('dataPM.csv','a')
#writing data to file, 
#data format from sensor = Time,Loc,PM1,PM2.5,PM4,PM10,TSP,Status
#W = data written in file, not uploaded
#U = data uploaded to thingspeak
	f.write(timestamp+","+data[2]+","+data[3]+","+data[4]+","+data[5]+","+data[6]+",W\n")

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
	f = open('dataPM.csv','rw+')
	lines = f.readlines()
	for i in xrange(len(lines)-1,-1,-1):	#start sorting from the latest data
		data = lines[i]
		data = data.split(",")
		timestamp = data[0]
		status = data[6]
		sent = 0
		if status != "U\n":
			sent = upload(timestamp, data[1], data[2], data[3], data[4], data[5])
			if sent == 1:
				lines[i]=lines[i].replace("W","U")

	f.seek(0)
	f.writelines(lines)
	f.close
	termgprs()
else:
	print ("GPRS Connection Initialization Failed")
