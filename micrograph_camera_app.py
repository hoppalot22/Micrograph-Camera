# Import required Libraries
import tkinter as tk
import numpy as np
from PIL import Image, ImageTk
import cv2
from tkinter import ttk
import sys
import os



# Create an instance of TKinter Window or frame
class MainWindow():
    def __init__(self):
    
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app 
            # path into variable _MEIPASS'.
            self.CURR_DIR= os.path.abspath(".")#sys._MEIPASS
        else:
            self.CURR_DIR = os.path.dirname(os.path.abspath(__file__))
        
        self.rowSpan = 20
        self.columnSpan = 5        
        
        #Create window
        self.win = tk.Tk()
        self.scale = "5x"
        self.imgName = "sample"
        self.scaleImage = (np.ones((20,160, 3), np.uint8)*255)
        self.magLabel = tk.Label(self.win, text = self.scale)
        self.magLabel.grid(row = self.rowSpan, column = 1)
        
        # Create a Label to capture the Video frames
        self.refresh = True
        self.camLabel = tk.Label(self.win)
        self.camLabel.grid(row=0, column=0, columnspan = self.columnSpan, rowspan = self.rowSpan)
        self.cameras = self.returnCameraIndexes()
        self.cameraDropdown = ttk.Combobox(self.win, values = self.cameras)
        self.cameraDropdown.bind("<<ComboboxSelected>>", self.onCameraChange)
        self.cameraDropdown.grid(row = self.rowSpan, column = 0)
        self.cap = cv2.VideoCapture(0)
        self.updateScale()
        
        #Buttons
        self.mag1 = ttk.Button(self.win, text = "5x", command = self.Mag1)
        self.mag2 = ttk.Button(self.win, text = "10x", command = self.Mag2)
        self.mag3 = ttk.Button(self.win, text = "20x", command = self.Mag3)
        self.mag4 = ttk.Button(self.win, text = "50x", command = self.Mag4)
        self.mag5 = ttk.Button(self.win, text = "100x", command = self.Mag5)
        #self.custom = ttk.Button(self.win, text = "Custom", command = self.Custom)
        #self.customForm = ttk.Entry(self.win)
        self.captureButton = ttk.Button(self.win, text = "Capture", command = self.CaptureImage)
        
        self.mag1.grid(row = 0, column = self.columnSpan)
        self.mag2.grid(row = 0, column = self.columnSpan + 1)
        self.mag3.grid(row = 0, column = self.columnSpan + 2)
        self.mag4.grid(row =0, column = self.columnSpan + 3)
        self.mag5.grid(row = 0, column = self.columnSpan + 4)
        #self.custom.grid(row = 5, column = 10)
        #self.customForm.grid(row = 6, column = 5)
        self.captureButton.grid(row = 1, column = self.columnSpan + 4)
        
    def Mag1(self):
        self.scale = "5x"            
    def Mag2(self):
        self.scale = "10x"  
    def Mag3(self):
        self.scale = "20x"  
    def Mag4(self):
        self.scale = "50x"  
    def Mag5(self):
        self.scale = "100x"
    def Custom(self):
        try:
            self.scale = int(self.customForm.get())
        except Exception as e:
            print(e)
        
    def updateScale(self):
      
        mag2scaleDist = {
        5 : 500,
        10: 200,
        20: 100,
        50: 20,
        100: 20,
        }
        
        


# Define function to show frame
    
    def CaptureImage(self):
        if not self.refresh:
            self.img.save(f"{self.CURR_DIR}//captures/{self.imgName}")
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
        # Get the latest frame and convert into Image
        cv2image = cv2.cvtColor(self.cap.read()[1],cv2.COLOR_BGR2RGB)
        w, h, d = self.scaleImage.shape
       
        cv2image[-1*(w):,-1*(h):, :] = self.scaleImage
        self.img = Image.fromarray(cv2image)

        # Convert image to PhotoImage
        imgtk = ImageTk.PhotoImage(image = self.img)
        self.img = imgtk
        self.camLabel.configure(image=imgtk)
        # Repeat after an interval to capture continiously
        if(self.refresh):
            self.camLabel.after(20, self.show_frames)

def Main():
    myWindow = MainWindow()
    myWindow.show_frames()
    myWindow.win.mainloop()

if __name__ == "__main__":
    Main()
