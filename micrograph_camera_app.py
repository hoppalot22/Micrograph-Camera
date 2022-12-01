# Import required Libraries
import tkinter as tk
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont
import cv2
from tkinter import ttk, filedialog
import sys
import os
import enum
import math


# Create an instance of TKinter Window or frame

class State(enum.Enum):
    default = 0
    measuring = 1
    calibrating = 2
class MainWindow():
    def __init__(self):


        self.knownDistLabel = None
        self.knownDistForm = None
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app 
            # path into variable _MEIPASS'.
            self.CURR_DIR= os.path.abspath(".")#sys._MEIPASS
        else:
            self.CURR_DIR = os.path.dirname(os.path.abspath(__file__))



        self.rowSpan = 20
        self.columnSpan = 10
        
        #Create window and bind events
        self.win = tk.Tk()
        self.win.title("MicroGraph Camera App")

        self.win.bind("<Button-1>", self.onLeftClick)
        self.win.bind("<Button-3>", self.onRightClick)
        self.win.bind("<B1-Motion>", self.onMouseDrag)
        self.win.bind("<ButtonRelease-1>", self.onLeftClickRelease)

        #Create "Global" variables
        self.saveDir = ''
        self.scale = "5x"
        self.imgName = "sample"
        self.imageBounds = [0,0,0,0]
        self.point1 = (0,0)
        self.point2 = (0,0)
        self.showLine = False
        self.pix2dist = 1
        self.state = State.default
        self.scaleImage = (np.ones((20,160, 3), np.uint8)*255)
        self.magLabel = tk.Label(self.win, text = self.scale)
        self.magLabel.grid(row = self.rowSpan, column = 1)
        self.calibrations = {
            "5x" : 1,
            "10x": .5,
            "20x": 0.25,
            "50x": 0.1,
            "100x": 0.05,
        }
        
        # Create a Label to capture the Video frames add some widgets
        self.refresh = True
        self.camLabel = tk.Label(self.win)
        self.camLabel.grid(row=0, column=0, columnspan = self.columnSpan, rowspan = self.rowSpan)
        self.distLabel = tk.Label(self.win, text="Dist:")
        self.distLabel.grid(row = self.rowSpan, column=2)
        self.cameras = self.returnCameraIndexes()
        self.cameraDropdown = ttk.Combobox(self.win, values = self.cameras)
        self.cameraDropdown.bind("<<ComboboxSelected>>", self.onCameraChange)
        self.cameraDropdown.grid(row = self.rowSpan, column = 0)

        self.repLabel = tk.Label(self.win, text="Rep number")
        self.metalLabel = tk.Label(self.win, text="Microstructure Region")
        self.detailLabel = tk.Label(self.win, text="Additional details")
        self.savePathLabel = tk.Label(self.win,text=f"Saving to:\n{self.CURR_DIR}\\captures")
        self.repLabel.grid(row = 3, column=self.columnSpan+2)
        self.metalLabel.grid(row=3, column=self.columnSpan + 3)
        self.detailLabel.grid(row=3, column=self.columnSpan + 4)
        self.savePathLabel.grid(row=5, column=self.columnSpan, columnspan=4)

        self.repNumBox = tk.Entry(self.win)
        self.repNumBox.grid(row = 4, column = self.columnSpan+2)
        self.metalSelectBox = ttk.Combobox(self.win, values = ["Parent Metal", "Weld Metal", "Coarse HAZ", "Fine HAZ"])
        self.metalSelectBox.grid(row = 4, column = self.columnSpan+3)
        self.extraDetailBox = tk.Entry(self.win)
        self.extraDetailBox.grid(row = 4, column = self.columnSpan+4)
        self.cap = cv2.VideoCapture(0)
        
        #Buttons
        self.mag1 = ttk.Button(self.win, text = "5x", command = self.Mag1)
        self.mag2 = ttk.Button(self.win, text = "10x", command = self.Mag2)
        self.mag3 = ttk.Button(self.win, text = "20x", command = self.Mag3)
        self.mag4 = ttk.Button(self.win, text = "50x", command = self.Mag4)
        self.mag5 = ttk.Button(self.win, text = "100x", command = self.Mag5)
        self.captureButton = ttk.Button(self.win, text = "Capture", command = self.CaptureImage)
        self.calibrateButton = ttk.Button(self.win, text = f"Calibrate {self.scale}", command=self.Calibrate)
        self.MeasureButton = ttk.Button(self.win, text="Measure", command=self.Measure)
        self.saveToButton = ttk.Button(self.win, text="SaveTo...", command=self.FileDialog)
        
        self.mag1.grid(row = 0, column = self.columnSpan)
        self.mag2.grid(row = 0, column = self.columnSpan + 1)
        self.mag3.grid(row = 0, column = self.columnSpan + 2)
        self.mag4.grid(row =0, column = self.columnSpan + 3)
        self.mag5.grid(row = 0, column = self.columnSpan + 4)
        self.captureButton.grid(row = 1, column = self.columnSpan + 4)
        self.calibrateButton.grid(row=1, column=self.columnSpan + 3)
        self.MeasureButton.grid(row=1, column=self.columnSpan + 2)
        self.saveToButton.grid(row = 1, column = self.columnSpan + 1)
        
    def Mag1(self):
        self.scale = "5x"
        self.magLabel.configure(text=self.scale)
        if not (self.knownDistForm is None):
            self.knownDistForm.destroy()
            self.knownDistLabel.destroy()
        self.calibrateButton.configure(text=f"Calibrate {self.scale}")
    def Mag2(self):
        self.scale = "10x"
        self.magLabel.configure(text=self.scale)
        if not (self.knownDistForm is None):
            self.knownDistForm.destroy()
            self.knownDistLabel.destroy()
        self.calibrateButton.configure(text=f"Calibrate {self.scale}")
    def Mag3(self):
        self.scale = "20x"
        self.magLabel.configure(text=self.scale)
        if not (self.knownDistForm is None):
            self.knownDistForm.destroy()
            self.knownDistLabel.destroy()
        self.calibrateButton.configure(text=f"Calibrate {self.scale}")
    def Mag4(self):
        self.scale = "50x"
        self.magLabel.configure(text=self.scale)
        if not (self.knownDistForm is None):
            self.knownDistForm.destroy()
            self.knownDistLabel.destroy()
        self.calibrateButton.configure(text=f"Calibrate {self.scale}")
    def Mag5(self):
        self.scale = "100x"
        self.magLabel.configure(text=self.scale)
        if not (self.knownDistForm is None):
            self.knownDistForm.destroy()
            self.knownDistLabel.destroy()
        self.calibrateButton.configure(text=f"Calibrate {self.scale}")


    def FileDialog(self):
        self.saveDir = filedialog.askdirectory()
        self.savePathLabel.configure(text=f"Save Directory: \n {self.saveDir}")
    def getLinePixDist(self):
        return round(math.sqrt((self.point2[0]-self.point1[0])*(self.point2[0]-self.point1[0]) + (self.point2[1]-self.point1[1])*(self.point2[1]-self.point1[1])))
    def Calibrate(self):
        if not (self.state == State.calibrating):
            self.state = State.calibrating
            self.calibrateButton.configure(text="Finish")
            self.MeasureButton.configure(text="Measure")
            self.knownDistLabel = tk.Label(self.win, text="Enter Known Distance \nIn Micrometers")
            self.knownDistForm = tk.Entry(self.win)
            self.knownDistLabel.grid(row = 2, column=self.columnSpan + 2)
            self.knownDistForm.grid(row = 2, column=self.columnSpan + 3)
        else:
            try:
                self.calibrations[self.scale] = round(float(self.knownDistForm.get())/self.getLinePixDist(),2)
                self.distLabel.configure(text=f"Calibration Success {self.calibrations[self.scale]} Micrometers per pixel at {self.scale} Magnification")
            except Exception as e:
                print(e, self.point1, self.point2)
                self.distLabel.configure(text=f"Calibration Failed")
            self.state = State.default
            self.showLine = False
            self.knownDistForm.destroy()
            self.knownDistLabel.destroy()
            self.calibrateButton.configure(text=f"Calibrate {self.scale}")

    def Measure(self):
        if not (self.state == State.measuring):
            self.state = State.measuring
            self.MeasureButton.configure(text="Finish")
            self.calibrateButton.configure(text=f"Calibrate {self.scale}")
        else:
            self.state = State.default
            self.MeasureButton.configure(text="Measure")
            self.showLine = False

    def onLeftClick(self,event):

        self.imageBounds = [self.camLabel.winfo_x()+1, self.camLabel.winfo_y()+1, self.camLabel.winfo_x()-1+self.camLabel.winfo_width(), self.camLabel.winfo_y()-1+self.camLabel.winfo_height()]
        if not ((self.imageBounds[0] < event.x < self.imageBounds[2]) and (self.imageBounds[1] < event.y < self.imageBounds[3])):
            return

        if not(str(event.widget) == r".!label2"):
            return

        if self.state == State.measuring or self.state == State.calibrating:
            self.point1 = (event.x, event.y)
            self.point2 = (event.x, event.y)
            self.showLine = True

    def onLeftClickRelease(self,event):
        if self.state == State.measuring or self.state == State.calibrating:
            self.distLabel.configure(text = f"Dist: {round(self.getLinePixDist()*self.calibrations[self.scale],2)} micrometers ({self.getLinePixDist()} pixels)")

    def onRightClick(self,event):
        self.showLine = False

    def onMouseDrag(self,event):
        if not ((self.imageBounds[0] < event.x < self.imageBounds[2]) and (self.imageBounds[1] < event.y < self.imageBounds[3])):
            return
        if self.state == State.measuring or self.state == State.calibrating:
            self.point2 = (event.x, event.y)

# Define function to show frame
    
    def CaptureImage(self):

        metalAbbreviations = {
            "Weld Metal" : "WM",
            "Parent Metal": "PM",
            "Coarse HAZ": "CGHAZ",
            "Fine HAZ": "FGHAZ"
        }
        if self.saveDir == '':
            self.savePathLabel.configure(text="Please choose a save directory before capturing image")
            return
        if not self.refresh:
            try:
                savePath = f"{self.saveDir}/R{str(self.repNumBox.get())} {metalAbbreviations[str(self.metalSelectBox.get())]}-{str(self.extraDetailBox.get().strip())}.jpg"
                if savePath[-5] == '-':
                    savePath = savePath[0:-5] + ".jpg"
                self.savePathLabel.configure(text=f"Saved to: \n {savePath}")
                self.img.save(savePath)
            except Exception as e:
                self.savePathLabel.configure(f"Error saving file \n{e}")

            self.captureButton.configure(text="Capture")
            self.refresh = True
            self.show_frames()
        else:
            self.refresh = False
            self.captureButton.configure(text = "Confirm")
        
    
    def onCameraChange(self, event):
        self.cap = cv2.VideoCapture(int(self.cameraDropdown.get().split()[-1]))


    def returnCameraIndexes(self):
        # checks the first 10 indexes.
        index = 0
        arr = []
        i = 10
        while i > 0:
            cap = cv2.VideoCapture(index)
            if cap.read()[0]:
                arr.append(f"Port {index}")
                cap.release()
            index += 1
            i -= 1
        return arr

    def show_frames(self):

        mag2scaleDist = {
        "5x" : 500,
        "10x": 200,
        "20x": 100,
        "50x": 20,
        "100x": 20,
        }
        # Get the latest frame and convert into Image
        cv2image = cv2.cvtColor(self.cap.read()[1],cv2.COLOR_BGR2RGB)
        self.img = Image.fromarray(cv2image).resize((1000, 800))
        scaleImgArray = np.ones((20,round(mag2scaleDist[self.scale]/self.calibrations[self.scale]), 3), np.uint8)*255
        scaleImgArray[:,0:2] = 0
        scaleImgArray[:, -3:-1] = 0
        self.scaleImage = Image.fromarray(scaleImgArray)

        ImageDraw.Draw(self.scaleImage).text((round(mag2scaleDist[self.scale]/self.calibrations[self.scale]/2 - 50), 5), f"{str(mag2scaleDist[self.scale])} Micrometers", (0,0,0))

        w = self.scaleImage.width
        h = self.scaleImage.height
       
        self.img.paste(self.scaleImage, (self.img.width - w, self.img.height - h))

        if self.showLine:
            ImageDraw.Draw(self.img).line([self.point1,self.point2], fill=0, width = 5)

        # Convert image to PhotoImage
        self.imgtk = ImageTk.PhotoImage(image = self.img)
        self.camLabel.configure(image=self.imgtk)
        # Repeat after an interval to capture continiously
        if(self.refresh):
            self.camLabel.after(20, self.show_frames)

def Main():
    myWindow = MainWindow()
    myWindow.show_frames()
    myWindow.win.mainloop()

if __name__ == "__main__":
    Main()
