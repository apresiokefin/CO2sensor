#!/usr/bin/python

import serial
import datetime
import time
import os

SIMstatus = 1
key = 'HHQEW2LE696EWKJ6'
ttySIM = '/dev/ttyATH0'

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
	time.sleep(2)
	response = rdln(simport)
	print(response)
	return response

#Longer waiting time ATcommand
def sdatcmdwait(val): 
	simport.write(atcmd[val])
	time.sleep(6)
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
		sdatcmdwait(8) #deactivating bearer
		response = sdatcmdwait(6) #reactivating bearer
		if response.find("ERROR") >= 0:
			SIMstatus = 0
			return SIMstatus
			print ("Bearer activation problem: unsolved!")

	response = sdatcmdwait(7) #AT+SAPBR=2,1
	if response.find("0.0.0.0") >= 0:
		SIMstatus = 0
		return SIMstatus
		print ("IP address not initialized!")
	
	response = sdatcmd(9) #AT+HTTPINIT
	if response.find("ERROR") >= 0:
		sdatcmdwait(13) #AT+HTTPTERM
		response = sdatcmdwait(9) #AT+HTTPINIT
		if response.find("ERROR") >= 0:
			SIMstatus = 0
			return SIMstatus
			print ("Initializing HTTP Service failed!")
	response = sdatcmd(10) #AT+HTTPPARA="CID",1
	if response.find("ERROR") >= 0:
		response = sdatcmdwait(10) #repeating input
		if response.find("ERROR") >= 0:
			SIMstatus = 0
			return SIMstatus
			print ("Identifying bearer profile failed!")

#terminating GPRS connection
def termgprs():
	sdatcmd(13) #AT+HTTPTERM
	sdatcmdwait(8) #AT+SAPBR=0,1

#function to upload data to Thingspeak using Sim800L
def upload(timestamp, pm1, pm25, pm4, pm10, tsp, ppm):
    while True:
	cmdupload="AT+HTTPPARA=\"URL\",\"http://api.thingspeak.com/update?api_key="+key+"&field1="+ppm+"&field2="+pm1+"&field3="+pm25+"&field4="+pm4+"&field5="+pm10+"&field6="+tsp+"&created_at="+timestamp+"&timezone=Asia/Jakarta\"\r"
	response = sdcmd(cmdupload)
	if response.find("ERROR") >= 0:
		print ("Upload failed!")
		break
	response = sdatcmdwait(11) #AT+HTTPACTION=0
	if response.find("200") >= 0: #OK
		print (ppm,pm1,pm25,pm4,pm10,tsp)
		print (timestamp)
		print ("OK")
		sent = 1
		return sent
		break	
	else:
		print "HTTP Connection failed"
		sent = 0
		return sent
		break

#check and define serial port for SIM800L
try:	
	simport = serial.Serial(ttySIM,9600, timeout=3.0)
	simportcheck = simport.isOpen()
	SIMstatus = 1
except (serial.serialutil.SerialException,OSError), error:
	SIMstatus = 0
	print (error)

#begin uploading procedure
if SIMstatus != 0:
	SIMstatus = initgprs()
else:
	print ("Check SIM800 serial connection")

#read and collect data from file
if SIMstatus != 0:
	f = file('datasensync.csv','r+b',os.O_NONBLOCK)
	lines = f.readlines()
	for i in xrange(len(lines)-1,-1,-1):	#start sorting from the latest data
		data = lines[i]
		data = data.split(",")
		timestamp = data[0]
		status = data[7]
		sent = 0
		if status != "U\n":
			sent = upload(timestamp, data[1], data[2], data[3], data[4], data[5], data[6])
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

