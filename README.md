# Introduction
This package is designed to make the TUCSEN SDK more user friendly and robust by defining an API for spectroscopists.
The classes and methods are desinged to be incorporated into a spectroscopic setup with other hardware. It is designed to be used with PyQt5 GUI, and has such dependencies, but these can be safely removed if undesired.

The SimulatedHardware class enables high-granularity simulation of the camera for testing, and includes a singal generating method to create a simulated laser signal on the detector. It has specific uses in my RamanMicrocsope codebase, and should prove useful when testing your camera integration.

Tested only on Dynana 400BSI V3, Windows 64bit.

# Example useage
A camera can be interfaced using:

from tucsencam import TucsenCamera
cam = TucsenCamera()

and controlled via methods such as:

cam.set_roi(tuple)
cam.set_hardware_binning()
cam.set_exposure_time(acqtime)
cam.set_target_temperature(-20)
cam.set_fan_speed(3)

Data is captured using:
#acquires immediately
image_data = cam.grab_frame() 
or
#waits for sensor temperature to drop below target specified in cam.initialise 
image_data = cam.grab_frame_safe()

the image_data is a 3D numpy array of dims [cam.roi[2], cam.roi[3], 1].

When interfacing with PyQt5 GUI elements, cam.temp_signal emits the temperature readout for the GUI to pick up.


