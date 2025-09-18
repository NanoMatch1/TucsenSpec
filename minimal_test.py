from src.tucsenspec.tucsencam import TucsenCamera
import numpy as np

def test_camera_operations():
    try:
        camera = TucsenCamera()
        camera.initialise()
        camera.set_exposure(0.2)
        frame = camera.grab_frame_safe()
        assert frame is not None
        assert type(frame) == np.ndarray
        assert frame.ndim == 3

    finally:
        camera.close_camera()

if __name__ == "__main__":
    test_camera_operations()