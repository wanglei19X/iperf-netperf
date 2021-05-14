#!/usr/bin/env python
#-*-coding:utf-8-*-

import os
import re
import sys
import threading
import time
import random
import subprocess
from CreateLogFile import CreateLogFile
from createSubWindows import createSubWindows

############################################################
#user file value.
ethNameList = [["enp1s0f0","enp1s0f1"]]           #testPortName,the first eth in the pare is server,the second is custom
tasksetCPU = [[10,11],[20,21]]                      #taskset cpu core
testBasicIP = ["192.168.10."]                       #base ip addr
testTime = 36000                                      #test time per cycle
loopTime = 3                                       #test cycle
testTypeList = ["tcp","udp"]
collectOpticalSec = 5
############################################################


'''
testCommand = {"tcp":{"server":"taskset -c %d stdbuf -oL iperf3 -s -1 -i 1 -p %s -B %s","custom":"taskset -c %d stdbuf -oL iperf3 -c %s -f M -i 1 -b 10000M -w 300k -t %d -p %s -B %s"},\
        "udp":{"server":"taskset -c %d stdbuf -oL iperf3 -s -1 -i 1 -p %s -B %s","custom":"taskset -c %d stdbuf -oL iperf3 -c %s -f M -i 1 -b 10000M -w 300k -u -t %d -p %s -B %s"}}
'''
testCommand = {"tcp":{"server":"stdbuf -oL iperf3 -s -1 -i 1 -p %s -B %s","custom":"stdbuf -oL iperf3 -c %s -f M -i 1 -b 10000M -w 300k -t %d -p %s -B %s"},\
        "udp":{"server":"stdbuf -oL iperf3 -s -1 -i 1 -p %s -B %s","custom":"stdbuf -oL iperf3 -c %s -f M -i 1 -b 10000M -w 300k -u -t %d -p %s -B %s"}}
TESTSCRIPTNAME = "OpticalLongStress"
ethInfoFileName = "testEthInfo.log"
opticalFileName = "opticalInfo.log"
opticalInfoSet = ("time","ethName","biascurrent","outputpower","receivepower","temperature","voltage")
opticalGrepStr = {"biascurrent":"laser bias current      ",\
                    "outputpower":"laser output power       ",\
                    "receivepower":"receiver signal average optical power  ",\
                    "temperature":"module temperature    ",\
                    "voltage":"module voltage     "}
testPareInfo = []
serverListenPort = []
iperfThreadSurvive = {}
__all__ = ["opticalLongStress"]


class opticalLongStress():
    def __init__(self,commandKey):
        global serverListenPort 
        #self.ethParameter = {"ethNameList":ethNameList,"ipaddr":ipAddr,"netMask":netMask,"NameSpace":[],"linkStat":[]}
        self.logFileObject = CreateLogFile(TESTSCRIPTNAME + commandKey)
        self.logPath = self.logFileObject.getLogPath()
        ethLinkStat = self.getEthStat()
        self.getPortNum()
        #print(testPareInfo)
        self.initStat = True
        self.mutex = threading.Lock()
        if ethLinkStat:
            self.setEthLookBack()
        else:
            self.initStat = False
    
    def getPortNum(self):
        global serverListenPort
        global ethNameList
        portIndex = len(ethNameList) * 2
        for index in range(portIndex):
            while True:
                randPortNum = random.randint(5000,9999)
                if os.popen("netstat -anp | grep %d" % randPortNum).read() == "":
                    serverListenPort.append(str(randPortNum))
                    break    
    def startTest(self,testType):
        global testPareInfoi
        global tasksetCPU
        global serverListenPort
        global printBuf
        global iperfThreadSurvive
        if self.initStat:
            customThreadList = []
            serverThreadList = []
            iperfThreadSurvive = {}
            for index,pearTest in enumerate(testPareInfo):
                serverThreadList.append(threading.Thread(target=self.startiPerfServer,args=(pearTest,serverListenPort[index],tasksetCPU[index][0],testType,)))
                customThreadList.append(threading.Thread(target=self.startiPerfCustom,args=(pearTest,serverListenPort[index],tasksetCPU[index][1],testType,)))
                iperfThreadSurvive[serverListenPort[index]] = True
            for customThread in serverThreadList:
                customThread.start()
            time.sleep(2)

            for serverThread in customThreadList:
                serverThread.start()
            getOpticalInfoLogThread = threading.Thread(target = self.getOpticalInfoLog)
            getOpticalInfoLogThread.start()
            iperfStat = True
            while iperfStat:                
                finishThread = 0
                for key in iperfThreadSurvive:
                    if iperfThreadSurvive[key]:
                        break
                    else:
                        finishThread = finishThread + 1
                    if finishThread == len(iperfThreadSurvive):
                        iperfStat = False
            self.monitorWindowObject.classClose()
        else:
            print("config error,please confirm and try it again.\n")
    
    def getOpticalInfoLog(self):
        global collectOpticalSec
        global opticalInfoSet
        opticalInfoLog = open(self.logPath + "/" + opticalFileName,"a")
        formatLine = "%-20s%-20s%-30s%-30s%-30s%-30s%-30s\n"
        opticalInfoLog.write(formatLine % opticalInfoSet)
        opticalInfoLog.close()
        global iperfThreadSurvive
        iperfStat = True
        while iperfStat:
            time.sleep(collectOpticalSec)
            lines = self.getOpticalInfo()
            opticalInfoLog = open(self.logPath + "/" + opticalFileName,"a")
            for line in lines:
                opticalInfoLog.write(formatLine % line)
            opticalInfoLog.close()
            finishThread = 0
            for key in iperfThreadSurvive:
                if iperfThreadSurvive[key]:
                    break
                else:
                    finishThread = finishThread + 1
                if finishThread == len(iperfThreadSurvive):
                    iperfStat = False

    def getOpticalInfo(self):
        global opticalInfoSet
        global opticalGrepStr
        opticalInfoList = []
        lineSet = set()
        for testPare in ethNameList:
            for ethName in testPare: 
                opticalInfoDict = {}
                #("time","ethName","biascurrent","outputpower","receivepower","temperature","voltage")
                opticalInfoDict["time"] = str(time.time())
                opticalInfoDict["ethName"] = ethName
                for key in opticalGrepStr:
                    opticalInfoDict[key] = self.getCommandInfo(opticalGrepStr[key],ethName)
                lineSet = (opticalInfoDict["time"],opticalInfoDict["ethName"],opticalInfoDict["biascurrent"],opticalInfoDict["outputpower"],\
                            opticalInfoDict["receivepower"],opticalInfoDict["temperature"],opticalInfoDict["voltage"])
                opticalInfoList.append(lineSet)
        return opticalInfoList

    def getCommandInfo(self,command,ethName):
        subp = subprocess.Popen("ethtool -m %s | grep -i \"%s\"" % (ethName,command),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        subp.wait()
        tempLine = subp.stdout.read()
        if tempLine != "":
            return tempLine.strip().split(":")[1]
        else:
            return "No value"
    def startiPerfServer(self,ethPareInfo,portNum,cpuCoreNum,testType):
        global testTime
        global testCommand
        command = testCommand[testType]["server"] % (portNum,ethPareInfo["serverIp"])
        os.system("echo %s >> cmd_file" % command)
        #print(command + "\n")
        testResultFile = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr = subprocess.PIPE,stdin = subprocess.PIPE,bufsize=1,universal_newlines=True)
        iPerftestResultLog = open(self.logPath + "/" + ethPareInfo["serverName"] + portNum + "_server.log","a")
        self.printInSubWindow(ethPareInfo["monitorServer"],"start server iperf %s" % (ethPareInfo["serverName"]))
        for line in iter(testResultFile.stdout.readline,b''):
            self.printInSubWindow(ethPareInfo["monitorServer"],"iperf3 server : " + line)
            iPerftestResultLog.write(line)
            if not testResultFile.poll() is None:
                #if line == "":
                if re.search(r"receiver",line,re.I):
                    break
	
        iPerftestResultLog.close()
        self.printInSubWindow(ethPareInfo["monitorServer"],"server done\n")

    def startiPerfCustom(self,ethPareInfo,portNum,cpuCoreNum,testType):
        global testTime
        global printBuf
        global iperfThreadSurvive
        command = testCommand[testType]["custom"] % (ethPareInfo["customRoute"],testTime,portNum,ethPareInfo["customIp"])
        os.system("echo %s >> cmd_file" % command)
        testResultFile = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr = subprocess.PIPE,stdin = subprocess.PIPE,bufsize=1,universal_newlines=True)
        iPerftestResultLog = open(self.logPath + "/" + ethPareInfo["customName"] + portNum + "_customer.log","a")
        self.printInSubWindow(ethPareInfo["monitorCustom"],"start custom iperf %s" % (ethPareInfo["customName"]))
        for line in iter(testResultFile.stdout.readline,b''):  
            self.printInSubWindow(ethPareInfo["monitorCustom"],"iperf3 custom %s: " % (portNum) + line)
            iPerftestResultLog.write(line)
            if not subprocess.Popen.poll(testResultFile) is None:
                self.printInSubWindow(ethPareInfo["monitorCustom"],line)
                if re.search(r"done",line,re.I) or re.search(r"error",line,re.I):
                #if line == "":
                    self.mutex.acquire(True)
                    iperfThreadSurvive[portNum] = False
                    self.mutex.release()
                    break
        iPerftestResultLog.close()
        self.printInSubWindow(ethPareInfo["monitorCustom"],"custom done\n")

    def outputBuffer(self,outputStr):
        self.printInSubWindow(outputStr["winObj"],outputStr["printStr"])
        #outputStr["winObj"].getkey() 


    def setEthLookBack(self):
        global ethNameList
        global testPareInfo
        global testBasicIP
        #os.system("iptables -t nat -F")
        windowList = []
        for pareIndex,testPareEth in enumerate(ethNameList):
            ethPareInfo = {}
            pareIp =  testBasicIP[pareIndex]
            ethPareInfo["serverIp"] = pareIp + "1"
            ethPareInfo["serverName"] = testPareEth[0]
            ethPareInfo["customName"] = testPareEth[1]
            ethPareInfo["customIp"] = pareIp + "2"
            ethPareInfo["customRoute"] = pareIp + "22"
            winTitleInfo = {}
            winTitleInfo["winName"] = ethPareInfo["customName"] + "-->" + ethPareInfo["serverName"] + ": customer"
            winTitleInfo["titleMessage"] = ethPareInfo["customIp"] + "-->" + ethPareInfo["serverIp"]
            windowList.append(winTitleInfo)
            winTitleInfo = {}
            winTitleInfo["winName"] = ethPareInfo["customName"] + "-->" + ethPareInfo["serverName"] + ": server"
            winTitleInfo["titleMessage"] = ethPareInfo["customIp"] + "-->" + ethPareInfo["serverIp"]
            windowList.append(winTitleInfo)
            testPareInfo.append(ethPareInfo)

            ethPareInfo = {}
            ethPareInfo["serverIp"] = pareIp + "2"
            ethPareInfo["serverName"] = testPareEth[1]
            ethPareInfo["customName"] = testPareEth[0]
            ethPareInfo["customIp"] = pareIp + "1"
            ethPareInfo["customRoute"] = pareIp + "11"
            winTitleInfo = {}
            winTitleInfo["winName"] = ethPareInfo["customName"] + "-->" + ethPareInfo["serverName"] + ": customer"
            winTitleInfo["titleMessage"] = ethPareInfo["customIp"] + "-->" + ethPareInfo["serverIp"]
            windowList.append(winTitleInfo)
            winTitleInfo = {}
            winTitleInfo["winName"] = ethPareInfo["customName"] + "-->" + ethPareInfo["serverName"] + ": server"
            winTitleInfo["titleMessage"] = ethPareInfo["customIp"] + "-->" + ethPareInfo["serverIp"]
            windowList.append(winTitleInfo)
            testPareInfo.append(ethPareInfo)

            cmd0 = "ip addr add %s/24 dev %s" % (pareIp + "1",testPareEth[0])
            cmd1 = "ip addr add %s/24 dev %s" % (pareIp + "2",testPareEth[1])
            cmd2 = "route add %s dev %s" % (pareIp + "11",testPareEth[0])
            cmd3 = "route add %s dev %s" % (pareIp + "22",testPareEth[1])
            cmd4 = "arp -i %s -s %s %s" % (testPareEth[0],pareIp + "11",self.getEthMacAddr(testPareEth[1]))
            cmd5 = "arp -i %s -s %s %s" % (testPareEth[1],pareIp + "22",self.getEthMacAddr(testPareEth[0]))
            cmd6 = "iptables -t nat -A POSTROUTING -s %s -d %s -j SNAT --to-source %s" % (pareIp + "1",pareIp + "11",pareIp + "22")
            cmd7 = "iptables -t nat -A PREROUTING -s %s -d %s -j DNAT --to-destination  %s" % (pareIp + "22",pareIp + "11",pareIp + "2")
            cmd8 = "iptables -t nat -A POSTROUTING -s %s -d %s -j SNAT --to-source %s" % (pareIp + "2",pareIp + "22",pareIp + "11")
            cmd9 = "iptables -t nat -A PREROUTING -s %s -d %s -j DNAT --to-destination %s" % (pareIp + "11",pareIp + "22",pareIp + "1")
            os.system("echo %s >> cmd_file" % cmd0)
            os.system("echo %s >> cmd_file" % cmd1)
            os.system("echo %s >> cmd_file" % cmd2)
            os.system("echo %s >> cmd_file" % cmd3)
            os.system("echo %s >> cmd_file" % cmd4)
            os.system("echo %s >> cmd_file" % cmd5)
            os.system("echo %s >> cmd_file" % cmd6)
            os.system("echo %s >> cmd_file" % cmd7)
            os.system("echo %s >> cmd_file" % cmd8)
            os.system("echo %s >> cmd_file" % cmd9)
            
            os.system("ip addr add %s/24 dev %s" % (pareIp + "1",testPareEth[0]))
            os.system("ip addr add %s/24 dev %s" % (pareIp + "2",testPareEth[1]))

            os.system("route add %s dev %s" % (pareIp + "11",testPareEth[0]))
            os.system("route add %s dev %s" % (pareIp + "22",testPareEth[1]))

            os.system("arp -i %s -s %s %s" % (testPareEth[0],pareIp + "11",self.getEthMacAddr(testPareEth[1])))
            os.system("arp -i %s -s %s %s" % (testPareEth[1],pareIp + "22",self.getEthMacAddr(testPareEth[0])))


            #print(self.getEthMacAddr(testPareEth[1]))
            #print(self.getEthMacAddr(testPareEth[0]))
            
            os.system("iptables -t nat -A POSTROUTING -s %s -d %s -j SNAT --to-source %s" % (pareIp + "1",pareIp + "11",pareIp + "22"))
            os.system("iptables -t nat -A PREROUTING -s %s -d %s -j DNAT --to-destination  %s" % (pareIp + "22",pareIp + "11",pareIp + "2"))
            os.system("iptables -t nat -A POSTROUTING -s %s -d %s -j SNAT --to-source %s" % (pareIp + "2",pareIp + "22",pareIp + "11"))
            os.system("iptables -t nat -A PREROUTING -s %s -d %s -j DNAT --to-destination %s" % (pareIp + "11",pareIp + "22",pareIp + "1"))
        #print(testPareInfo)
        #print(windowList)
        self.createMonitorWindow(windowList)
        #next = raw_input("please enter to do next")

    def createMonitorWindow(self,windowList):
        global testPareInfo
        #start create sub windows
        self.monitorWindowObject = createSubWindows(windowList)
        try:
            for index in range(len(testPareInfo)):
                testPareInfo[index]["monitorCustom"] = self.monitorWindowObject.windowObjList[index * 2]["winObj"]
                testPareInfo[index]["monitorServer"] = self.monitorWindowObject.windowObjList[index * 2 + 1]["winObj"]
            #self.printList(testPareInfo)
        except Exception as e:
            self.monitorWindowObject.classClose()
            print(e)
    def printInSubWindow(self,winObj,outStr):
        self.mutex.acquire(True)           
        self.monitorWindowObject.printStrInWindow(winObj,outStr)
        self.mutex.release()

    def printList(self,list):
        for str in list:
            print(str, "\n")
    def getEthStat(self):
        global ethNameList
        global ethInfoFileName
        ethLinkList = []
        ethInfoFile = open(self.logPath + "/" +ethInfoFileName,"w")
        for testPare in ethNameList:
            linkStatDict = {}
            for ethName in testPare:
                #os.system("ip netns del %s" % ethName)
                #os.system("systemctl restart network.service")
                ethInfoRes = os.popen("ethtool %s" % ethName).read()
                linkStat = re.search("speed.+[0-9]{2,2}.+\n",ethInfoRes,re.I)
                print(linkStat)
                if linkStat != "":
                    try:
                        linkStatDict[ethName] = linkStat.group().split("\n")[0].split(":")[1].strip()
                        ethInfoFile.writelines(ethInfoRes)
                    except Exception as e:
                        print(e)
                else:
                    linkStatDict[ethName] = ""
                    ethInfoFile.close()
                    return False
            ethLinkList.append(linkStatDict)
        ethInfoFile.close()
        return ethLinkList
                
    def getEthMacAddr(self,ethName):
        ethInfo = os.popen("ip addr show dev  %s" % (ethName)).read()
        macRes = re.search(r"[[0-9a-f]{2,2}:[0-9a-f:]+:[0-9a-f]{2,2}",ethInfo,re.I)
        if macRes:
            return macRes.group()
        else:
            return False


if __name__ == '__main__':

    # cpu and memory
    #os.system("stress --cpu 55 -i 4 --vm 10 --vm-bytes 1G --vm-hang 100 --timeout %s &" % testTime)
    #time.sleep(5)

    # fio
    #os.system()
    os.system("clear")
    time.sleep(5)
    testPareInfo = []
    # network
    opticalLongStressTest = opticalLongStress("tcp")
    opticalLongStressTest.startTest("tcp")
