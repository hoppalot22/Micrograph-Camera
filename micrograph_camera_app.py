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
import time


#TODO
#Implement on screen measurements for images.

# Create an instance of TKinter Window or frame

class State(enum.Enum):
    default = 0
    measuring = 1
    calibrating = 2


class MainWindow:
    def __init__(self):

        self.knownDistLabel = None
        self.knownDistForm = None
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app 
            # path into variable _MEIPASS'.
            self.CURR_DIR = os.path.abspath(".")  # sys._MEIPASS
        else:
            self.CURR_DIR = os.path.dirname(os.path.abspath(__file__))

        if os.path.exists(f"{self.CURR_DIR}\\cals"):
            self.init_text = "Calibration Labels read from 'cals' file"
            self.calibrations = {}
            with open(f"{self.CURR_DIR}\\cals") as cal_file:
                calList = []
                for line in cal_file.readlines():
                    calList.append(line.split("="))
                    self.calibrations[calList[-1][0]] = float(calList[-1][1])
        else:
            self.init_text = "Calibrations not read from file, using default values, cals file has been created"
            self.calibrations = {
                "5x": 1,
                "10x": .5,
                "20x": 0.25,
                "50x": 0.1,
                "100x": 0.05,
            }
            self.save_calibration()

        self.rowSpan = 20
        self.columnSpan = 10

        # Create window and bind events
        self.win = tk.Tk()
        self.win.title("MicroGraph Camera App")

        self.win.bind("<Button-1>", self.onLeftClick)
        self.win.bind("<Button-3>", self.onRightClick)
        self.win.bind("<B1-Motion>", self.onMouseDrag)
        self.win.bind("<ButtonRelease-1>", self.onLeftClickRelease)

        # Create "Global" variables
        self.screenShape = [self.win.winfo_screenwidth(), self.win.winfo_screenheight()]
        self.customCal = None
        self.saveDir = ''
        self.scale = "5x"
        self.imgName = "sample"
        self.imageBounds = [0, 0, 0, 0]
        self.point1 = (0, 0)
        self.point2 = (0, 0)
        self.showLine = False
        self.pix2dist = 1
        self.state = State.default
        self.scaleImage = (np.ones((20, 160, 3), np.uint8) * 255)
        self.magLabel = tk.Label(self.win, text=self.scale)
        self.magLabel.grid(row=self.rowSpan, column=1)

        # Buttons
        self.buttonWidth = 12
        
        self.mag1 = ttk.Button(self.win, text="5x", command=self.Mag1, width = self.buttonWidth)
        self.mag2 = ttk.Button(self.win, text="10x", command=self.Mag2, width = self.buttonWidth)
        self.mag3 = ttk.Button(self.win, text="20x", command=self.Mag3, width = self.buttonWidth)
        self.mag4 = ttk.Button(self.win, text="50x", command=self.Mag4, width = self.buttonWidth)
        self.mag5 = ttk.Button(self.win, text="100x", command=self.Mag5, width = self.buttonWidth)
        self.customButton = ttk.Button(self.win, text="Custom Mag", command=self.CustomMag, width = self.buttonWidth)
        self.captureButton = ttk.Button(self.win, text="Capture", command=self.CaptureImage, width = self.buttonWidth)
        self.calibrateButton = ttk.Button(self.win, text=f"Calibrate {self.scale}", command=self.Calibrate, width = self.buttonWidth)
        self.MeasureButton = ttk.Button(self.win, text="Measure", command=self.Measure, width = self.buttonWidth)
        self.saveToButton = ttk.Button(self.win, text="SaveTo...", command=self.FileDialog, width = self.buttonWidth)
        self.retryCamButton = ttk.Button(self.win, text = "Retry Camera", command = self.retryCam)

        self.mag1.grid(row=0, column=self.columnSpan)
        self.mag2.grid(row=0, column=self.columnSpan + 1)
        self.mag3.grid(row=0, column=self.columnSpan + 2)
        self.mag4.grid(row=0, column=self.columnSpan + 3)
        self.mag5.grid(row=0, column=self.columnSpan + 4)
        self.customButton.grid(row=0, column=self.columnSpan + 5)
        self.captureButton.grid(row=1, column=self.columnSpan + 4)
        self.calibrateButton.grid(row=1, column=self.columnSpan + 3)
        self.MeasureButton.grid(row=1, column=self.columnSpan + 2)
        self.saveToButton.grid(row=1, column=self.columnSpan + 1)
        self.retryCamButton.grid(row = 3, column = self.columnSpan)


        # Create a Label to capture the Video frames add some widgets
        self.refresh = True
        self.camLabel = tk.Label(self.win)
        self.camLabel.grid(row=0, column=0, columnspan=self.columnSpan, rowspan=self.rowSpan)
        self.distLabel = tk.Label(self.win, text=self.init_text)
        self.distLabel.grid(row=self.rowSpan, column=2)
        self.cameras = self.returnCameraIndexes()
        self.cameraDropdown = ttk.Combobox(self.win, values=self.cameras)
        self.cameraDropdown.current(0)
        self.cameraDropdown.bind("<<ComboboxSelected>>", self.onCameraChange)
        self.cameraDropdown.grid(row=self.rowSpan, column=0)

        self.repLabel = tk.Label(self.win, text="Rep\nnumber")
        self.metalLabel = tk.Label(self.win, text="Microstructure\nRegion")
        self.detailLabel = tk.Label(self.win, text="Additional\ndetails")
        self.savePathLabel = tk.Label(self.win, text=f"Select a save directory")
        self.repLabel.grid(row=3, column=self.columnSpan + 2)
        self.metalLabel.grid(row=3, column=self.columnSpan + 3)
        self.detailLabel.grid(row=3, column=self.columnSpan + 4)
        self.savePathLabel.grid(row=5, column=self.columnSpan, columnspan=10)
        
        self.fixedScaleBool = tk.BooleanVar()
        self.fixedScale = tk.Checkbutton(self.win, text = "Fixed Scale", variable=self.fixedScaleBool, onvalue=True, offvalue=False)
        self.fixedScale.grid(row = 1, column = self.columnSpan)
        self.customMagBox = tk.Entry(self.win, width = self.buttonWidth)
        self.customMagBox.grid(row=1, column=self.columnSpan + 5)
        self.repNumBox = tk.Entry(self.win, width = self.buttonWidth)
        self.repNumBox.grid(row=4, column=self.columnSpan + 2)
        self.metalSelectBox = ttk.Combobox(self.win, values=["Parent Metal", "Weld Metal", "Coarse HAZ", "Fine HAZ"], width = self.buttonWidth)
        self.metalSelectBox.grid(row=4, column=self.columnSpan + 3)
        self.extraDetailBox = tk.Entry(self.win, width = self.buttonWidth)
        self.extraDetailBox.grid(row=4, column=self.columnSpan + 4)
        self.cap = cv2.VideoCapture(0)



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

    def CustomMag(self):
        try:
            custMag = int(self.customMagBox.get())
            self.scale = f"{custMag}x"
            self.magLabel.configure(text=self.scale)
            self.calibrations[self.scale] = 5/custMag

            if not (self.knownDistForm is None):
                self.knownDistForm.destroy()
                self.knownDistLabel.destroy()
            self.calibrateButton.configure(text=f"Calibrate {self.scale}")
        except Exception as e:
            print (e)

    def UpdateSavePath(self, path):
        n = 30
        spot = 0
        newPath = ""
        for i, substring in enumerate(path.split("/")):
            if len(newPath) > n+spot:
                newPath += "\n"
                spot = len(newPath)
            newPath += substring + "\\"
        self.saveDir = path
        self.savePathLabel.configure(text=f"Save Directory: \n {newPath}")

    def FileDialog(self):
        self.UpdateSavePath(filedialog.askdirectory())

    def getLinePixDist(self):
        return round(math.sqrt((self.point2[0] - self.point1[0]) * (self.point2[0] - self.point1[0]) + (
                    self.point2[1] - self.point1[1]) * (self.point2[1] - self.point1[1])))

    def Calibrate(self):
        if not (self.state == State.calibrating):
            self.state = State.calibrating
            self.calibrateButton.configure(text="Finish")
            self.MeasureButton.configure(text="Measure")
            self.knownDistLabel = tk.Label(self.win, text="Enter Known Distance \nIn Micrometers")
            self.knownDistForm = tk.Entry(self.win)
            self.knownDistLabel.grid(row=2, column=self.columnSpan + 2)
            self.knownDistForm.grid(row=2, column=self.columnSpan + 3)
        else:
            try:
                self.calibrations[self.scale] = round(float(self.knownDistForm.get()) / self.getLinePixDist(), 2)
                self.distLabel.configure(
                    text=f"Calibration Success {self.calibrations[self.scale]} Micrometers per pixel at {self.scale} Magnification")
                self.save_calibration()

            except Exception as e:
                print(e, self.point1, self.point2)
                self.distLabel.configure(text=f"Calibration Failed")
            self.state = State.default
            self.showLine = False
            self.knownDistForm.destroy()
            self.knownDistLabel.destroy()
            self.calibrateButton.configure(text=f"Calibrate {self.scale}")

    def save_calibration(self):
        try:
            with open(f"{self.CURR_DIR}\\cals", 'w') as cal_file:
                for cal in self.calibrations:
                    cal_file.write(f"{cal}={self.calibrations[cal]}\n")
        except Exception as e:
            self.distLabel.configure(text = f"Error saving cals:\n {e}")
            print(e)

    def Measure(self):
        if not (self.state == State.measuring):
            self.state = State.measuring
            self.MeasureButton.configure(text="Finish")
            self.calibrateButton.configure(text=f"Calibrate {self.scale}")
        else:
            self.state = State.default
            self.MeasureButton.configure(text="Measure")
            self.showLine = False

    def onLeftClick(self, event):

        self.imageBounds = [self.camLabel.winfo_x() + 1, self.camLabel.winfo_y() + 1,
                            self.camLabel.winfo_x() - 1 + self.camLabel.winfo_width(),
                            self.camLabel.winfo_y() - 1 + self.camLabel.winfo_height()]
        if not ((self.imageBounds[0] < event.x < self.imageBounds[2]) and (
                self.imageBounds[1] < event.y < self.imageBounds[3])):
            return

        if not (str(event.widget) == r".!label2"):
            return

        if self.state == State.measuring or self.state == State.calibrating:
            self.point1 = (event.x, event.y)
            self.point2 = (event.x, event.y)
            self.showLine = True

    def onLeftClickRelease(self, event):
        if self.state == State.measuring or self.state == State.calibrating:
            self.distLabel.configure(
                text=f"Dist: {round(self.getLinePixDist() * self.calibrations[self.scale], 2)} micrometers ({self.getLinePixDist()} pixels)")

    def onRightClick(self, event):
        self.showLine = False
        if not self.refresh:
            self.refresh = True
            self.captureButton.configure(text="Capture")
            self.show_frames()
            return

    def onMouseDrag(self, event):
        if not ((r".!label2" in str(event.widget)) and(self.imageBounds[0] < event.x < self.imageBounds[2]) and (
                self.imageBounds[1] < event.y < self.imageBounds[3])):
            return
        if self.state == State.measuring or self.state == State.calibrating:
            self.point2 = (event.x, event.y)

    # Define function to show frame

    def CaptureImage(self):

        if self.saveDir == '':
            self.savePathLabel.configure(text="Please choose a save directory before capturing image")
            return
            
        self.refresh = False
        self.captureButton.configure(text="Confirm", command = self.ConfirmImage)

    def ConfirmImage(self):
        metalAbbreviations = {
            "Weld Metal": "WM",
            "Parent Metal": "PM",
            "Coarse HAZ": "CGHAZ",
            "Fine HAZ": "FGHAZ"
        }
        try:
            repString = str(self.repNumBox.get()).replace('/','\\').replace('\\','')
            metalString = str(metalAbbreviations[str(self.metalSelectBox.get().replace('/','\\').replace('\\',''))])
            detailString = str(self.extraDetailBox.get().strip().replace('/','\\').replace('\\',''))
            savePath = f"{self.saveDir}/R{repString} {metalString}-{detailString}.jpg"
            if savePath[-5] == '-':
                savePath = savePath[0:-5] + ".jpg"
            
            if os.path.isfile(savePath):
                if tk.messagebox.askyesno(title = "Overwrite?", message = "Filename already exists, would you like to overwrite?"):
                    self.UpdateSavePath("\\".join(savePath.replace("/","\\").split("\\")[0:-1]))
                    self.img.save(savePath)
            
            else:
                self.UpdateSavePath("\\".join(savePath.replace("/","\\").split("\\")[0:-1]))
                self.img.save(savePath)
            
        except Exception as e:
            self.savePathLabel.configure(f"Error saving file \n{e}")
            print(e)

        self.captureButton.configure(text="Capture", command = self.CaptureImage)
        self.refresh = True
        self.show_frames()

    def onCameraChange(self, event):
        self.cap.release()
        self.cap = cv2.VideoCapture(int(self.cameraDropdown.get().split()[-1]))

    def retryCam(self):    
        self.cap.release()
        self.cameras = self.returnCameraIndexes()
        self.cameraDropdown.configure(values=self.cameras)
        self.cameraDropdown.current(0)
        self.cap = cv2.VideoCapture(int(self.cameraDropdown.get().split()[-1]))
        if not self.refresh:
            self.refresh = True
            self.camLabel.after(10, self.show_frames)

    def returnCameraIndexes(self):
        # checks the first 10 indexes.
        index = 0
        arr = []
        i = 10
        delay = 10
        time_init = time.time()
       
        while ((i > 0)):
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.read()[0]:
                arr.append(f"Port {index}")
            cap.release()
            index += 1
            i -= 1
        return arr

    def show_frames(self):

        mag2scaleDist = {"5x": 500, "10x": 200, "20x": 100, "50x": 40, "100x": 20}
        if self.scale not in mag2scaleDist:
            mag2scaleDist[self.scale] = 50
        scaleMult = 150*self.calibrations[self.scale]/mag2scaleDist[self.scale]
        # Get the latest frame and convert into Image
        try:
            cv2image = cv2.cvtColor(self.cap.read()[1], cv2.COLOR_BGR2RGB)
        except Exception as e:
            if (tk.messagebox.askretrycancel(title = "Video Capture Error", message = f"Following error occured while trying to access camera\n{e}\n Try reconnecting the camera and clicking retry.")):
                self.retryCam()
            else:
                self.refresh = False
            return
        self.img = Image.fromarray(cv2image).resize((int(self.screenShape[0]/2), 3*int(self.screenShape[1]/4)))
        if self.fixedScaleBool.get() == False:
            scaleMult = 1
        scaleLength = round(scaleMult*mag2scaleDist[self.scale] / self.calibrations[self.scale])

        scaleImgArray = np.ones((20, scaleLength, 3), np.uint8) * 255
        scaleImgArray[:, 0:2] = 0
        scaleImgArray[:, -3:-1] = 0
        self.scaleImage = Image.fromarray(scaleImgArray)

        ImageDraw.Draw(self.scaleImage).text(
            (round(scaleLength / 2 - 50), 5),
            f"{str(round(scaleMult*mag2scaleDist[self.scale]))} Micrometers", (0, 0, 0))

        w = self.scaleImage.width
        h = self.scaleImage.height

        self.img.paste(self.scaleImage, (self.img.width - w, self.img.height - h))

        if self.showLine:
            ImageDraw.Draw(self.img).line([self.point1, self.point2], fill=0, width=5)

        # Convert image to PhotoImage
        self.imgtk = ImageTk.PhotoImage(image=self.img)
        self.camLabel.configure(image=self.imgtk)
        # Repeat after an interval to capture continiously
        if (self.refresh):
            self.camLabel.after(10, self.show_frames)


def Main():
    myWindow = MainWindow()
    myWindow.show_frames()
    myWindow.win.mainloop()


if __name__ == "__main__":
    Main()
