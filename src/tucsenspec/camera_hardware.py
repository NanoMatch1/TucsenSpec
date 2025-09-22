import ctypes
import numpy as np
import time

from contextlib import contextmanager
from ctypes import byref, c_void_p, c_int32, c_uint32, c_int, c_double

from tucsenspec.tucam_ret import check_ok, summarize, is_success

from ctypes import pointer, cast, POINTER
from tucsenspec.TUCam import (
    TUCAM_ROI_ATTR,
    TUCAM_Buf_Alloc,
    TUCAM_Buf_Release,
    TUCAM_Buf_WaitForFrame,
    TUCAM_Buf_AbortWait,
    TUCAM_Cap_Start,
    TUCAM_Cap_Stop,
    TUCAM_Capa_SetValue,
    TUCAM_Prop_SetValue,
    TUCAM_Dev_Open,
    TUCAM_Dev_Close,
    TUCAM_Api_Init,
    TUCAM_Api_Uninit,
    TUCAM_IDCAPA,
    TUCAM_IDPROP,
    TUCAM_Cap_SetROI,
    TUCAM_Prop_GetValue,
    TUCAM_Capa_GetValue,
    TUCAM_FILE_SAVE,
    TUCAM_FRAME,
    TUIMG_FORMATS,
    TUFRM_FORMATS,
    TUCAM_CAPTURE_MODES,
    TUCAM_OPEN,
    TUCAMRET,
    TUCAM_INIT,
    # TUIDC_PIXELCLOCK,
    # TUIDC_ROLLINGSCANMODE,
    # TUIDC_ENABLEOVERLAP,
    # TUIDC_IMGMODESELECT,
    # TUIDC_ATEXPOSURE
)

TUCAM_Prop_SetValue.argtypes = [c_void_p, c_int32, c_double, c_int32]
TUCAM_Prop_SetValue.restype  = c_uint32
TUCAM_Capa_SetValue.argtypes = [c_void_p, c_int32, c_int32]
TUCAM_Capa_SetValue.restype  = c_uint32

class TucamData:
    def __init__(self):
        self.data = None
        self.m_fs = TUCAM_FILE_SAVE()
        self.m_frame = TUCAM_FRAME()
        self.m_format = TUIMG_FORMATS
        self.m_frformat = TUFRM_FORMATS
        self.m_capmode = TUCAM_CAPTURE_MODES
        self.m_frame.pBuffer = 0
        self.m_frame.ucFormatGet = TUFRM_FORMATS.TUFRM_FMT_USUAl.value
        self.m_frame.uiRsdSize = 1
        self.m_fs.nSaveFmt = self.m_format.TUFMT_TIF.value

class CameraHardwareBase:
    def open_stream(self): raise NotImplementedError
    def close_stream(self): raise NotImplementedError
    def grab_frame(self): raise NotImplementedError
    def initialise(self): raise NotImplementedError
    def set_exposure_time(self, value): raise NotImplementedError
    def set_image_and_gain(self, img_mode, gain_level): raise NotImplementedError
    def set_image_processing(self, value): raise NotImplementedError
    def set_resolution(self, resolution): raise NotImplementedError
    def set_denoise(self, value): raise NotImplementedError
    def set_fan_speed(self, speed): raise NotImplementedError
    def get_fan_speed(self): raise NotImplementedError
    def enable_auto_temperature_control(self, enable): raise NotImplementedError
    def set_target_temperature(self, target_celsius): raise NotImplementedError
    def get_temperature(self): raise NotImplementedError
    def set_roi(self, roi_tuple): raise NotImplementedError
    def close_camera(self): raise NotImplementedError
    def open_camera(self): raise NotImplementedError
    def uninit_api(self): raise NotImplementedError


class RealHardware(CameraHardwareBase):
    """Real hardware interface for Tucsen cameras using the TUCam SDK."""
    
    def __init__(self, camera):
        self.camera = camera
        self.interface = camera.interface
        self.logger = camera.logger.getChild('RealHardware')
        self.scriptDir = self.interface.scriptDir
        self._stream_open = False
        self.conflag = TUCAMRET.TUCAMRET_SUCCESS

        self.data = TucamData()

    def init_capabilities(self):
        # int capabilities:
        TUCAM_Capa_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDCAPA.TUIDC_PIXELCLOCK.value, c_int32(0))   # e.g., 1
        TUCAM_Capa_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDCAPA.TUIDC_ROLLINGSCANMODE.value, c_int32(0))               # enable rolling scan if that’s default
        TUCAM_Capa_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDCAPA.TUIDC_ENABLEOVERLAP.value, c_int32(0))               # disable overlap for sCMOS if unstable
        # TUCAM_Capa_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDCAPA.TUIDC_IMGMODESELECT.value, c_int32(1))               # match your XML default (1)
        TUCAM_Capa_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDCAPA.TUIDC_ATEXPOSURE.value, c_int32(0))               # manual exposure

    def import_extra_functions(self):
        from tucsenspec.extra_functions import TUextra
        self.extra = TUextra(self.camera)
    
    def run_extra_functions(self):
        self.extra.camera_info()
        self.extra.get_camera_parameters()
        self.extra.get_gain_attributes()


    def dbg_dump(self):
        def gcap(id_):
            v = c_int32()
            TUCAM_Capa_GetValue(self.TUCAMOPEN.hIdxTUCam, id_, byref(v))
            return v.value
        def gprop(id_):
            v = c_double()
            TUCAM_Prop_GetValue(self.TUCAMOPEN.hIdxTUCam, id_, byref(v), 0)
            return v.value
        

        self.logger.info("RES={} PIXCLK={} IMG_MODE={} ATEXP={}".format(
            gcap(TUCAM_IDCAPA.TUIDC_RESOLUTION.value),
            gcap(TUCAM_IDCAPA.TUIDC_PIXELCLOCK.value),
            gcap(TUCAM_IDCAPA.TUIDC_IMGMODESELECT.value),
            # gcap(TUCAM_IDCAPA.TUIDC_ENABLEOVERLAP.value),
            gcap(TUCAM_IDCAPA.TUIDC_ATEXPOSURE.value)))
        self.logger.info("EXPO_ms={}".format(
            gprop(TUCAM_IDPROP.TUIDP_EXPOSURETM.value)))
            # gprop(TUCAM_IDPROP.TUIDP_FRAME_RATE.value)))


    def minimal_initialise(self):
        self.TUCAMINIT = TUCAM_INIT(0, self.scriptDir.encode('utf-8'))
        ret = TUCAM_Api_Init(pointer(self.TUCAMINIT), 5000)
        if not check_ok(ret, context="API init (minimal_initialise)", logger=self.logger):
            return

        self.open_camera()
        # self.set_image_processing(0)
        # self.set_resolution(1)
        # self.set_image_and_gain(5, 1)
        self.set_roi(self.camera.roi)
        self.set_target_temperature(-20)
        self.set_fan_speed(3)
        # self.set_exposure_time(self.camera.acqtime)
        # self.set_roi(self.camera.roi)
        self.open_stream()

    def initialise(self):
        self.TUCAMINIT = TUCAM_INIT(0, self.scriptDir.encode('utf-8'))
        ret = TUCAM_Api_Init(pointer(self.TUCAMINIT), 5000)
        if not check_ok(ret, context="API init (initialise)", logger=self.logger):
            return

        self.open_camera()
        self.set_hardware_binning()
        # self.set_auto_exposure(0)
        self.set_exposure_time(self.camera.acqtime)
        self.set_image_processing(0)
        self.set_resolution(1)
        self.set_image_and_gain(1, 0)
        self.set_roi(self.camera.roi)
        self.set_target_temperature(-20)
        self.set_fan_speed(3)

        self.open_stream()

    def open_stream(self):
        if self._stream_open:
            self.logger.debug("WARNING: tucam.open_stream: Stream is already open. Safely ignore if booting up.")
            return
        ret_buff = TUCAM_Buf_Alloc(self.TUCAMOPEN.hIdxTUCam, pointer(self.data.m_frame))
        if not check_ok(ret_buff, context="allocate frame buffer", logger=self.logger):
            return
    
        ret_start = TUCAM_Cap_Start(self.TUCAMOPEN.hIdxTUCam, self.data.m_capmode.TUCCM_SEQUENCE.value)
        if not check_ok(ret_start, context="start capture", logger=self.logger):
            return

        self._stream_open = True

    def close_stream(self):
        ret_abort = TUCAM_Buf_AbortWait(self.TUCAMOPEN.hIdxTUCam)
        check_ok(ret_abort, context="abort wait for buffer", logger=self.logger)

        ret_stop = TUCAM_Cap_Stop(self.TUCAMOPEN.hIdxTUCam)
        check_ok(ret_stop, context="stop capture", logger=self.logger)

        ret_release = TUCAM_Buf_Release(self.TUCAMOPEN.hIdxTUCam)
        check_ok(ret_release, context="release buffer", logger=self.logger)

        self._stream_open = False

    def grab_frame(self, timeout=50000):
        ret = TUCAM_Buf_WaitForFrame(self.TUCAMOPEN.hIdxTUCam, pointer(self.data.m_frame), timeout)
        if not check_ok(ret, context="wait for frame", logger=self.logger):
            return None

        if not self.data.m_frame.pBuffer:
            self.logger.error("TUCAM: Frame buffer pointer is null.")
            return None

        if self.data.m_frame.usWidth == 0 or self.data.m_frame.usHeight == 0:
            self.logger.error("TUCAM: Invalid frame dimensions received.")
            return None

        image = self._frame_to_numpy()
        return image

    def _frame_to_numpy(self):
        total_size = self.data.m_frame.usHeader + self.data.m_frame.uiImgSize
        raw_bytes = np.ctypeslib.as_array(
            cast(self.data.m_frame.pBuffer, POINTER(ctypes.c_ubyte)),
            shape=(total_size,)
        )
        img_bytes = raw_bytes[self.data.m_frame.usHeader: self.data.m_frame.usHeader + self.data.m_frame.uiImgSize]
        img_data = np.frombuffer(img_bytes.tobytes(), dtype=np.uint16)
        expected_elements = self.data.m_frame.usWidth * self.data.m_frame.usHeight * self.data.m_frame.ucChannels
        if img_data.size != expected_elements:
            self.logger.warning("Image element mismatch")
        try:
            return np.reshape(img_data, (self.data.m_frame.usHeight, self.data.m_frame.usWidth, self.data.m_frame.ucChannels))
        except Exception as e:
            self.logger.error(f"Reshape failed: {e}")
            return None
        
    def set_auto_exposure(self, state=0):
        """ Set the auto exposure state of the camera. Disabled by default. """
        ret = TUCAM_Capa_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDCAPA.TUIDC_ATEXPOSURE.value, state)
        check_ok(ret, context=f"set auto exposure (state={state})", logger=self.logger)

    def set_exposure_time(self, value_s):
        self.close_stream()

        ret1 = TUCAM_Capa_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDCAPA.TUIDC_ATEXPOSURE.value, 0)
        if not check_ok(ret1, context="disable auto exposure before set exposure", logger=self.logger):
            return False
        
        ms = float(value_s) * 1000.0  # convert seconds -> milliseconds, preserve fractions
        ret = TUCAM_Prop_SetValue(self.TUCAMOPEN.hIdxTUCam,
                                    TUCAM_IDPROP.TUIDP_EXPOSURETM.value,
                                    c_double(ms),  # pass double BY VALUE
                                    0)
        if not check_ok(ret, context=f"set exposure time (ms={ms:.3f})", logger=self.logger):
            return False
        
        self.open_stream()
        return True

    def set_image_and_gain(self, img_mode, gain_level):
        ret_set = TUCAM_Capa_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDCAPA.TUIDC_IMGMODESELECT.value, img_mode)
        check_ok(ret_set, context=f"set image mode (mode={img_mode})", logger=self.logger)

        ret_gain = TUCAM_Prop_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDPROP.TUIDP_GLOBALGAIN.value, gain_level, 0)
        check_ok(ret_gain, context=f"set global gain (level={gain_level})", logger=self.logger)

    def set_image_processing(self, value):
        ret = TUCAM_Capa_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDCAPA.TUIDC_ENABLEIMGPRO.value, value)
        check_ok(ret, context=f"set image processing (enable={value})", logger=self.logger)

    def set_denoise(self, value):
        ret = TUCAM_Capa_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDCAPA.TUIDC_ENABLEDENOISE.value, value)
        check_ok(ret, context=f"set denoise (enable={value})", logger=self.logger)

    def set_resolution(self, resolution):
        ret = TUCAM_Capa_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDCAPA.TUIDC_RESOLUTION.value, resolution)
        check_ok(ret, context=f"set resolution (value={resolution})", logger=self.logger)

    def set_fan_speed(self, speed):
        ret = TUCAM_Capa_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDCAPA.TUIDC_FAN_GEAR.value, speed)
        check_ok(ret, context=f"set fan speed (gear={speed})", logger=self.logger)

    def get_fan_speed(self):
        val = ctypes.c_int()
        ret = TUCAM_Capa_GetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDCAPA.TUIDC_FAN_GEAR.value, byref(val))
        if not check_ok(ret, context="get fan speed", logger=self.logger):
            return None
        return val.value

    def get_exposure_time(self):
        val = ctypes.c_double()
        ret = TUCAM_Prop_GetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDPROP.TUIDP_EXPOSURETM.value, byref(val), 0)
        if not check_ok(ret, context="get exposure time", logger=self.logger):
            return None
        return val.value / 1000.0  # convert ms to seconds

    def enable_auto_temperature_control(self, enable):
        val = 1 if enable else 0
        ret = TUCAM_Prop_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDPROP.TUIDP_AUTO_CTRLTEMP.value, val, 0)
        check_ok(ret, context=f"set auto temperature control (enable={enable})", logger=self.logger)

    def set_target_temperature(self, target_celsius):
        prop_val = int(max(-50, min(50, float(target_celsius))) + 50)
        ret = TUCAM_Prop_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDPROP.TUIDP_TEMPERATURE.value, prop_val, 0)
        check_ok(ret, context=f"set target temperature (C={target_celsius})", logger=self.logger)

    def get_temperature(self):
        temp = ctypes.c_double()
        ret = TUCAM_Prop_GetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDPROP.TUIDP_TEMPERATURE.value, byref(temp), 0)
        if not check_ok(ret, context="get temperature", logger=self.logger):
            return None
        return temp.value

    def set_roi(self, roi_tuple):
        self.close_stream()

        roi = TUCAM_ROI_ATTR()
        roi.bEnable = 1
        roi.nHOffset, roi.nVOffset, roi.nWidth, roi.nHeight = roi_tuple
        ret = TUCAM_Cap_SetROI(self.TUCAMOPEN.hIdxTUCam, roi)
        if not check_ok(ret, context=f"set ROI {roi_tuple}", logger=self.logger):
            return
        
        self.open_stream()  # NOTE: resetting the ROI restarts the stream.

    def set_hardware_binning(self, binning_level=1):
        ret = TUCAM_Capa_SetValue(self.TUCAMOPEN.hIdxTUCam, TUCAM_IDCAPA.TUIDC_RESOLUTION.value, binning_level)
        check_ok(ret, context=f"set hardware binning (level={binning_level})", logger=self.logger)

    def open_camera(self, Idx=0):
        if  Idx >= self.TUCAMINIT.uiCamCount:
            self.logger.error(f"TUCAM: Invalid camera index {Idx}. Available cameras: {self.TUCAMINIT.uiCamCount}. Check Camera is connected.")
            return

        self.logger.info('Opening camera...')
        self.TUCAMOPEN = TUCAM_OPEN(Idx, 0)

        ret = TUCAM_Dev_Open(pointer(self.TUCAMOPEN))
        if not check_ok(ret, context="open device", logger=self.logger):
            self.TUCAMOPEN.hIdxTUCam = 0
            return

        if 0 == self.TUCAMOPEN.hIdxTUCam:
            self.logger.info('Open the camera failure!')
            return
        else:
            self.logger.info('Open the camera success!')

    def close_camera(self):
        if self.TUCAMOPEN.hIdxTUCam:
            ret = TUCAM_Dev_Close(self.TUCAMOPEN.hIdxTUCam)
            check_ok(ret, context="close device", logger=self.logger)
            if check_ok(ret, context="close device (final check)", logger=self.logger):
                self.logger.info("Camera closed.")
            self.TUCAMOPEN.hIdxTUCam = 0

    
    def uninit_api(self):
        ret = TUCAM_Api_Uninit()
        check_ok(ret, context="API uninit", logger=self.logger)


class SimulatedHardware(CameraHardwareBase):
    def __init__(self, camera):
        self.camera = camera
        self.interface = camera.interface
        self.logger = camera.logger.getChild('SimulatedHardware')
        self.acqtime = 0.5
        self.roi = (0, 1220, 2048, 148)

    def initialise(self):
        self.logger.info("Simulated camera initialized")
        self.camera.save_transient_spectrum_cb = self.interface.acq_ctrl.save_spectrum_transient

    def open_stream(self):
        self.logger.info("[SIM] open_stream() called.")

    def close_stream(self):
        self.logger.info("[SIM] close_stream() called.")

    def grab_frame(self, timeout=100000):
        self.logger.coms("[SIM] grab_frame() called.")
        image_data = self._generate_simulated_image()
        time.sleep(self.acqtime)
        return image_data

    def get_temperature(self):
        return np.random.uniform(-20, -16)

    def set_exposure_time(self, value):
        try:
            self.acqtime = float(value)
            return True
        except ValueError:
            self.logger.error("[SIM] Invalid exposure time value")
            return False

    def set_image_and_gain(self, img_mode, gain_level):
        self.logger.debug("[SIM] set_image_and_gain() stub.")

    def set_image_processing(self, value):
        self.logger.debug("[SIM] set_image_processing() stub.")

    def set_denoise(self, value):
        self.logger.debug("[SIM] set_denoise() stub.")

    def set_resolution(self, resolution):
        self.logger.debug("[SIM] set_resolution() stub.")

    def set_fan_speed(self, speed):
        self.logger.debug("[SIM] set_fan_speed() stub.")

    def get_fan_speed(self):
        return 3  # simulate high speed by default

    def enable_auto_temperature_control(self, enable):
        self.logger.debug(f"[SIM] Auto temperature control {'enabled' if enable else 'disabled'}.")

    def set_target_temperature(self, target_celsius):
        self.logger.info(f"[SIM] Target temperature set to {target_celsius}°C")

    def set_roi(self, roi_tuple):
        self.logger.info(f"[SIM] ROI set to {roi_tuple}")
        self.roi = roi_tuple

    def close_camera(self):
        self.logger.debug("[SIM] close_camera() stub.")

    def open_camera(self):
        self.logger.debug("[SIM] open_camera() stub.")

    def uninit_api(self):
        self.logger.debug("[SIM] uninit_api() stub.")

    @property
    def randomise_laser(self):
        try:
            return not self.interface.microscope.laser_calibrated
        except Exception as e:
            self.logger.debug(f"[SIM] Laser calibration check failed: {e}")
            return True

    def _generate_simulated_laser_signal(self, width=2048, height=148, laser_position=None, wavelength_axis=None, laser_width=5, y_spread=20, peak_height=30000, peak_sigma=0.1):
        if self.interface.laser.status != 'ON' or self.interface.laser.current_power < 3:
            self.logger.coms("[SIM] Laser is off or power too low; signal zero.")
            return np.zeros((height, width), dtype=np.float32)

        wavelength_axis = self.interface.microscope.wavelength_axis
        if laser_position:
            laser_wavelength = laser_position
        elif self.interface.microscope.laser_calibrated:
            laser_wavelength = self.interface.microscope.laser_wavelength_calibrated
        else:
            laser_wavelength = self.interface.microscope.laser_wavelengths.get('l1', 785)

        Y, X = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')

        if laser_wavelength is not None and wavelength_axis is not None:
            index = np.argmin(abs(wavelength_axis - laser_wavelength))
            if index == 0 or index == len(wavelength_axis) - 1:
                self.logger.debug("[SIM] Laser out of range; signal zero.")
                return np.zeros((height, width), dtype=np.float32)
            if self.randomise_laser:
                laser_position = np.random.randint(index - 25, index + 25)
            else:
                laser_position = index
        else:
            laser_position = np.random.randint(0, width)

        laser_signal = np.exp(-0.5 * ((X - laser_position) / laser_width) ** 2) * \
                       np.exp(-0.5 * ((Y - height / 2) / y_spread) ** 2)

        scale = np.abs(np.random.normal(peak_height, peak_height * peak_sigma))
        laser_signal *= scale
        self.logger.coms(f"[SIM] Simulated laser wavelength: {wavelength_axis[laser_position] if wavelength_axis is not None else laser_position} nm")
        return laser_signal

    def _generate_simulated_image(self, width=2048, height=148):
        wavelength_axis = self.interface.microscope.wavelength_axis
        if wavelength_axis is None:
            wavelength_axis = np.arange(width).astype(int)
        background = 4000
        laser_signal = self._generate_simulated_laser_signal(width=width, height=height)
        noise = np.random.randint(-300, 300, laser_signal.shape)
        spectrum_image = background + laser_signal + noise
        spectrum_image = np.clip(spectrum_image, 0, 65535).astype(np.uint16)
        return spectrum_image