#!/usr/bin/env python

'''
winList: the sub window attribute,the attribute define as dict:
    winAttribute = {
    winName:""
    Titlemessage:""
}
'''
import curses, traceback
import time
import os
import subprocess
import math

WINDOWCOL = 2

__all__ = ["createSubWindows"]


class createSubWindows():
    #windowObjList = []
    def __init__(self,winList):
        windowNum = len(winList)
        consoleHeight,consoleWidth = self.getConsoleSize()
        if windowNum // WINDOWCOL == 0:
            column = windowNum
        else:
            column = WINDOWCOL
        row = int(math.ceil(windowNum/WINDOWCOL))

        windowHeight = int((consoleHeight-row) // row)
        windowWidth = int((consoleWidth-column) / column)
        #print(windowHeight,windowWidth,row,column)
        self.subWindowInit(consoleHeight,consoleWidth)
        self.windowObjList = self.createWindowByNum(windowHeight,windowWidth,column,row,winList)


    def getConsoleSize(self):
        consoleSize = subprocess.check_output(["stty","size"]).split("\n")[0]
        consoleHeight = int(consoleSize.split(" ")[0])
        consoleWidth = int(consoleSize.split(" ")[1])
        return(consoleHeight,consoleWidth)

    def subWindowInit(self,consoleHeight,consoleWidth):
        try:
            # Initialize curses()
	    self.stdscrObj = curses.initscr()
            self.Topwin=curses.newwin(consoleHeight,consoleWidth)
            # Turn off echoing of keys, and enter cbreak mode,
            # where no buffering is performed on keyboard input
            curses.noecho()
            curses.cbreak()
            # In keypad mode, escape sequences for special keys
            # (like the cursor keys) will be interpreted and
            # a special value like curses.KEY_LEFT will be returned
            self.stdscrObj.keypad(1)

        except:
            # In event of error, restore terminal to sane state.
            self.stdscrObj.keypad(0)
            curses.echo()
            curses.nocbreak()
            curses.endwin()
            traceback.print_exc()
            #Prinit the exception


    def classClose(self):
        self.stdscrObj.keypad(0)
        curses.echo()
        curses.nocbreak()
        #self.Topwin.endwin()
        curses.endwin()
        traceback.print_exc()

    def createWindow(self,paraWin,winHeight,winWidth,winBeginY,winBeginX):
        window = paraWin.subpad(winHeight,winWidth,winBeginY,winBeginX)
        window.border()
        #window.idlok(True)
        window.scrollok(True)
	window.idlok(True)
        return window

    def printStrInWindow(self,winObj,outPut):
        winObj.addstr(outPut)
        winObj.refresh()

    def createWindowByNum(self,windowHeight,windowWidth,column,row,winList):
        windowObjList = []
        createdNum = 0
        for rowIndex in range(row):
            for columnIndex in range(column):
                if createdNum < len(winList):
                    subWinObj = {}
                    winBeginY = rowIndex * windowHeight + 1
                    winBeginX = columnIndex * windowWidth + 1
                    #print(rowIndex,columnIndex,windowHeight,windowWidth,winBeginY,winBeginX)
                    #self.Topwin.getkey()
                    #create para window,put title and message
                    paraWinObj,titleRow = self.createTitleWindow(self.Topwin,windowHeight,windowWidth,winBeginY,winBeginX,winList[createdNum])
                    subWinHeight = windowHeight - titleRow - 2
                    subWinBeginY = winBeginY + titleRow + 1
                    subWinObj["winName"] = winList[createdNum]["winName"]
                    #print(subWinHeight,windowWidth,subWinBeginY,winBeginX)
                    #self.Topwin.getkey()
                    #time.sleep(2)
                    subWinObj["winObj"] = self.createWindow(paraWinObj,subWinHeight,windowWidth-1,subWinBeginY,winBeginX)
                    self.printStrInWindow(subWinObj["winObj"],"information display window created successed\n") 
                    windowObjList.append(subWinObj)
                    createdNum = createdNum + 1
        
        return windowObjList
    def createTitleWindow(self,paraWin,windowHeight,windowWidth,winBeginY,winBeginX,winTitleDict):
        winObj = self.createWindow(paraWin,windowHeight,windowWidth,winBeginY,winBeginX)
        self.printStrInWindow(winObj,winTitleDict["winName"] + "\n")
        self.printStrInWindow(winObj,winTitleDict["titleMessage"] + "\n")
        messageRow = int(math.ceil(len(winTitleDict["titleMessage"])/windowWidth) + 1)
        return (winObj,messageRow)



if __name__ == '__main__':
    winList = [{"winName":"custom","titleMessage":"this is customer"},{"winName":"server","titleMessage":"this is server"},{"winName":"custom2","titleMessage":"this is customer2"},{"winName":"server2","titleMessage":"this is server"}]
    createSubWindowstest = createSubWindows(winList)
    try:
        for i in range(5):
            for windowIndex,window in enumerate(createSubWindowstest.windowObjList):
                for index in range(17):
                    createSubWindowstest.printStrInWindow(window["winObj"],"windowNum: %s print line %d\n" % (window["winName"],index))
            createSubWindowstest.windowObjList[0]["winObj"].getkey()
        createSubWindowstest.classClose()
    except Exception as e:
        createSubWindowstest.classClose()
        print(e)
