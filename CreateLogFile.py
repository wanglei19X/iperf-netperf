#!/usr/bin/env python
'''
author information:
name:zhangdaoyong 
date:Nov 23 2020
version:1.0
'''

'''import module'''
import os
import sys
import time

__all__ = ["CreateLogFile"]

class CreateLogFile():
    def __init__(self,scriptName,isSelfCreate = True,isForce = None,path = None):
        if not path:
            self.logFolderPath = os.getcwd() + "/"
        else:
            self.logFolderPath = path + "/"
        self.logFolderName = "[" + self.getCurrentTimeAttr() + "]" + scriptName
        if isSelfCreate == True:
            if isForce == True:
                self.forceCreatelogFolder()
            else:
                self.createLogFolder()
            
    def createSubLogFolder(self,parentPath,subPathName):
        if subPathName in os.listdir(parentPath):
            os.system("rm -rf %s" % (parentPath + "/" + subPathName))
        os.system("mkdir %s" % (parentPath + "/" + subPathName))
        return parentPath + "/" + subPathName

    def createLogFolder(self):
        if self.logFolderName in os.listdir(os.getcwd()):
            if raw_input("Log folder has exist, first delete it(yes/no)") == "yes":
                os.system("rm -rf %s" % (self.logFolderPath + self.logFolderName))
            else:
                print("Log folder will be cover.")
        os.system("mkdir %s" % (self.logFolderPath + self.logFolderName))
    def forceCreatelogFolder(self):
        if self.logFolderName in os.listdir(os.getcwd()):
            os.system("rm -rf %s" % (self.logFolderName))
        os.system("mkdir %s" % (self.logFolderName))
    def getlogFolderPath(self):
        return self.logFolderPath + self.logFolderName
    def getCurrentTimeAttr(self):
        currentTime = time.gmtime(time.time())
        if currentTime.tm_mon < 10:
            month = "0" + str(currentTime.tm_mon)
        else:
            month = str(currentTime.tm_mon)
        if currentTime.tm_mday < 10:
            day = "0" + str(currentTime.tm_mday)
        else:
            day = str(currentTime.tm_mday)
        if currentTime.tm_hour < 10:
            hour = "0" + str(currentTime.tm_hour)
        else:
            hour = str(currentTime.tm_hour)
        if currentTime.tm_min < 10:
            minute = "0" + str(currentTime.tm_min)
        else:
            minute = str(currentTime.tm_min)
        logTime = str(currentTime.tm_year) + month + day + hour + minute
        return logTime
    def getLogPath(self):
        return str(os.getcwd() + "/" + self.logFolderName)
    def getLogPathName(self):
        return self.logFolderName
    def getLogFolderName(self):
        return self.logFolderName