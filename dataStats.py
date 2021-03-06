# dataStats.py
#
# acquire the data and start running some basic statistics
#
# LKS, June 2016 part of Insight Data Science Program
#
import numpy as np
import pandas as pd
import psycopg2
import sys
import matplotlib.pyplot as plt
import os
import plottingFunctions as pf
import webScrapeFunctions as WS
import datetime
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

#
# load in the data from the data base
def loadData(username, password, location, instartDate=0, inendDate=0):
       #
       # username = entered username
       # password = user password
       # location = their current location
       # instarDate = date from which to scrape and update from 
       #
       con = None
       con = psycopg2.connect(dbname='postgres', user='loisks',\
                              password='poppy33')
       # make it create individual data base
       dbname='polar'
       con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
           
       #
       # fetch the data
       
       try:
           con2 = psycopg2.connect("dbname='polar' user='loisks'")  
           cur=con2.cursor()
           #
           # FETCH THE DATA
           
           if instartDate != '':
                  print("The in start Date is: "+ str(instartDate))
                  startDt=datetime.datetime.strptime(instartDate,'%Y%m%d')
                  endDt=datetime.datetime.strptime(inendDate,'%Y%m%d')
                  curDt=startDt
                  #
                  # set up table
                  # Table Items are:
                  # StepsElement,ActiveTimeElement,DistanceElement,\
                  # CaloriesElement,AmountSleepElement, AmountGoodSleep,meanTemperature, \
                  # maxTemperature, minTemperature, precipitation, wind
                  #
    
                  curDt = startDt
                  while curDt != endDt:
    # 
    
                         #
                         # get the Activity data first
                         dateLink=datetime.datetime.strftime(curDt,'%d'+'.'+'%m'+'.'+'%Y')
                         url2='https://flow.polar.com/training/day/'+dateLink
                         print(curDt)
                         activeData=WS.getTrackerData(url2) # returns a dictionary
                         print('Acquired Activity Tracker Data')
                         weatherData=WS.getWeatherData(curDt, location)  # returns a list
                         print('Acquired Weather Data')
                         
                         #
                         # fix the hours string
                         temp1=activeData[1]
                         tt=temp1.index('h'); mm1=temp1.index('s'); mm2=temp1.index('m')
                         hours=int(temp1[0:tt-1]); minutes = int(temp1[mm1+2:mm2-1])
                         activeData[1]=hours+(minutes/100.) # hour + decimal fraction
                         
                         temp2=activeData[4]
                         tt=temp2.index('h'); mm1=temp2.index('s'); mm2=temp2.index('m')
                         hours=int(temp2[0:tt-1]); minutes = int(temp2[mm1+2:mm2-1])
                         activeData[4]=hours+(minutes/100.) # hour + decimal fraction
                         
                         # GET ACTIVITY AND PERCENT SLEEP BETTER    
                         
                         # add directly to data base
                         #dateq=datetime.datetime.strftime(curDt, '%Y%m%d')
                         query = 'INSERT INTO ' + username +' (DATE,STEPS,ACTIVETIME, DISTANCE,\
                         CALORIES, SLEEP, GOODSLEEP, MEANTEMPERATURE, \
                         MAXTEMPERATURE, MINTEMPERATURE, PRECIPITATION, WIND) VALUES (%s, %s, %s, %s, \
                         %s, %s, %s, %s, %s, %s, %s, %s);'
                         data=( curDt, float(activeData[0]), activeData[1], float(activeData[2]), \
                                int(activeData[3]), activeData[4], int(activeData[5]), weatherData[0], \
                                weatherData[1], weatherData[2], weatherData[3], weatherData[4])
                         print data
                         cur.execute(query,data)
                         con2.commit()
                         curDt+=datetime.timedelta(days=1)

                     
           cur.execute("SELECT * FROM loisks")#"+username) # access data currently in data base 
           AllUserData=cur.fetchall()
       except(None):
           print 'get the data base!'
       #
       # figure out if two dimensional here, swap the axes
       #
       # now put into pandas
       Parameters=['Steps', 'ActiveTime', 'Distance', 'Calories', \
               'Sleep', 'GoodSleep','MeanTemperature', 'MaxTemperature', \
               'MinTemperature','Precip', 'Wind']
       Labels=['Steps', 'Active Time [hours]', 'Distance [km]', 'Calories', \
               'Sleep [Hours]', 'Percentage Good Sleep', 'Average Temperature [F]', \
               'Max Temperature [F]', 'Min Temperature', 'Precipitation [inches]', \
               'Wind [mph]']
       #Parameters=['Calories', 'MeanTemperature', 'Precip', 'Wind']
       #Labels=['Calories', 'Average Temperature [F]', 'Precipitation [inches]', \
       #        'Wind [mph]']
       dates=pd.DatetimeIndex(np.swapaxes(AllUserData, 1,0)[0])
       dataOnly=np.swapaxes(np.swapaxes(AllUserData,1,0)[1:],1,0)
       df=pd.DataFrame(dataOnly, columns=Parameters)
       
       # clean the entire data frame!
       df=df.replace(1e-31, np.nan)
       #activeList=['Calories']
       #weatherList=['MeanTemperature', 'Precip', 'Wind']
       #activeLabels=['Calories']
       #weatherLabels=['Average Temperature [F]', 'Precipitation [inches]', 'Wind [mph]']
       activeList=['Steps', 'ActiveTime', 'Distance', 'Calories', \
               'Sleep', 'GoodSleep']
       weatherList=['MeanTemperature', 'MaxTemperature', 
               'MinTemperature','Precip', 'Wind']
       activeLabels=['Steps', 'Active Time [hours]', 'Distance [km]', 'Calories', \
               'Sleep [Hours]', 'Percentage Good Sleep']
       weatherLabels=['Average Temperature [F]', \
               'Max Temperature [F]', 'Min Temperature', 'Precipitation [inches]', \
               'Wind [mph]']
       # get rid of the zeros in the polar loop data 
       for iParam in range(len(activeList)):
           df[activeList[iParam]]=df[activeList[iParam]].replace(0,np.nan)
       
       #df['Precip'][df['Precip']>5]=np.nan # change this later? 
       df['Dates']=df.index
       df['week_days']=dates.dayofweek
       
       data=pf.plotter(activeList, weatherList, activeLabels, weatherLabels, \
                       'polar', username, location, color='purple')
       cals=data.CalPredict
       bestCorr=data.bestCorr
       bestDay=data.bestDay
       
       return(cals,bestCorr,bestDay) 



