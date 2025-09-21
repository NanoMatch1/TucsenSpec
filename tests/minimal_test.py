from tucsenspec.tucsencam import TucsenCamera
from tucsenspec.simulated_camera import DummyInterface
import numpy as np

def test_camera_simulated():
    try:
        camera = TucsenCamera(DummyInterface(), simulate=True)
        camera.initialise()
        camera.set_exposure_time(0.2)
        print("Eexposure success")
        camera.get_temperature()
        print("Get temperature success")
        camera.get_fan_speed()
        print("Get fan speed success")
        frame = camera.grab_frame_safe()
        assert frame is not None
        assert type(frame) == np.ndarray
        assert frame.ndim == 2  

    finally:
        camera.close_camera()

def test_camera_operations():
    try:
        camera = TucsenCamera(DummyInterface())
        
        camera.minimal_initialise()
        # camera.set_exposure_time(0.2)
        # print("Eexposure success")
        # camera.get_temperature()
        # print("Get temperature success")
        # camera.get_fan_speed()
        # print("Get fan speed success")
        # breakpoint()
        frame = camera.grab_frame_safe()
        assert frame is not None
        assert type(frame) == np.ndarray
        assert frame.ndim == 2  

    finally:
        camera.close_camera()

if __name__ == "__main__":
    test_camera_operations()