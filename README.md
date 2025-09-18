# Introduction
This package is designed to make the TUCSEN SDK more user friendly and robust by defining an API for spectroscopists.
The classes and methods are desinged to be incorporated into a spectroscopic setup with other hardware. It is designed to be used with PyQt5 GUI, and has such dependencies, but these can be safely removed if undesired.

Tested only on , Windows 64bit.

# Installation

1. Clone this repository.
2. Ensure the required DLLs are present in `tucsen/lib/x64` or `tucsen/lib/x86` depending on your system architecture.
3. Install dependencies:
	```bash
	pip install -r requirements.txt
	```
	Main dependencies: `PyQt5`, `numpy`.

# Supported Platforms

- Windows 64-bit (tested)
- Other platforms: Linux support is experimental. Ensure you have the correct shared library (`.so`) if using Linux.

**Hardware:** Dynana 400BSI V3 (tested). Other TUCSEN cameras should be supported thanks to the TUCam API, but this is not tested.

# DLL Requirements

- The main DLL required is `TUCam.dll`. Other DLLs (e.g., `msvcp120.dll`, `tuimgcv_core2410.dll`) may be needed for full functionality. Place all DLLs in the appropriate subfolder (`x64` or `x86`).

# Python Compatibility

- Tested with Python 3.11. Other versions may work but are not guaranteed.

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

# Simulated Camera

Use `SimulatedHardware` for testing without physical hardware. It can generate synthetic signals for development and debugging.


