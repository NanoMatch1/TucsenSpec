#!/usr/bin/env python
# coding: utf-8
'''
Created on 2024-01-03
@author:fdy
'''

import ctypes
from ctypes import *
from tucsenspec.TUCam import *
from enum import Enum
import time
import os

class Tucam():
    def __init__(self):
        self.Path  = os.path.dirname(os.path.abspath(__file__))
        self.TUCAMINIT = TUCAM_INIT(0, self.Path.encode('utf-8'))
        self.TUCAMOPEN = TUCAM_OPEN(0, 0)
        print('Initializing API (15s timeout)...', flush=True)
        init_ret = TUCAM_Api_Init(pointer(self.TUCAMINIT), 15000)
        print(f"ApiInit ret={init_ret}")
        print(self.TUCAMINIT.uiCamCount)
        print(self.TUCAMINIT.pstrConfigPath)
        print('Connect %d camera' % self.TUCAMINIT.uiCamCount, flush=True)
        # Some cameras need extra time to become ready after init
        time.sleep(2)

    def OpenCamera(self, Idx):
        if  Idx >= self.TUCAMINIT.uiCamCount:
            return
        self.TUCAMOPEN = TUCAM_OPEN(Idx, 0)
        print('Opening camera...', flush=True)
        open_ret = TUCAM_Dev_Open(pointer(self.TUCAMOPEN))
        print(f"DevOpen ret={open_ret}", flush=True)
        if 0 == self.TUCAMOPEN.hIdxTUCam:
            print('Open the camera failure!')
            return
        else:
            print('Open the camera success!')

    def CloseCamera(self):
        if 0 != self.TUCAMOPEN.hIdxTUCam:
            print('Closing camera...', flush=True)
            close_ret = TUCAM_Dev_Close(self.TUCAMOPEN.hIdxTUCam)
            print(f"DevClose ret={close_ret}", flush=True)
        print('Close the camera success', flush=True)

    def UnInitApi(self):
        print('Uninitializing API...', flush=True)
        TUCAM_Api_Uninit()

    def WaitForImageData(self):
        m_frame = TUCAM_FRAME()
        m_format = TUIMG_FORMATS
        m_frformat = TUFRM_FORMATS
        m_capmode = TUCAM_CAPTURE_MODES
        m_frame.pBuffer = 0
        m_frame.ucFormatGet = m_frformat.TUFRM_FMT_USUAl.value
        m_frame.uiRsdSize = 1
        print('Allocating buffer...', flush=True)
        alloc_ret = TUCAM_Buf_Alloc(self.TUCAMOPEN.hIdxTUCam, pointer(m_frame))
        print(f"BufAlloc ret={alloc_ret}", flush=True)
        print('Starting capture...', flush=True)
        start_ret = TUCAM_Cap_Start(self.TUCAMOPEN.hIdxTUCam, m_capmode.TUCCM_SEQUENCE.value)
        print(f"CapStart ret={start_ret}", flush=True)
        # Give camera a moment after starting capture
        time.sleep(0.1)
        nTimes = 10
        try:
            for i in range(nTimes):
                # First few frames can take longer; ramp timeout slightly
                timeout_ms = 3000 if i < 2 else 2000
                try:
                    result = TUCAM_Buf_WaitForFrame(self.TUCAMOPEN.hIdxTUCam, pointer(m_frame), timeout_ms)
                    code = int(result)
                except Exception:
                    code = 0x80000208
                # SDK success codes: 1 (SUCCESS), 2 (RECEIVE_FINISH), 3 (EXTERNAL_TRIGGER)
                if code in (int(TUCAMRET.TUCAMRET_SUCCESS.value), int(TUCAMRET.TUCAMRET_RECEIVE_FINISH.value), int(TUCAMRET.TUCAMRET_EXTERNAL_TRIGGER.value)):
                    print(
                        "Grab success: i=%d w=%d h=%d ch=%d bpp=%d size=%d" % (
                            i, m_frame.usWidth, m_frame.usHeight, m_frame.ucChannels, m_frame.ucElemBytes, m_frame.uiImgSize
                        ),
                        flush=True,
                    )
                else:
                    # Map a few common errors if possible
                    mapped = None
                    try:
                        for e in TUCAMRET:
                            if int(e.value) == code:
                                mapped = e
                                break
                    except Exception:
                        pass
                    print(f"Grab failure: i={i} ret={code} mapped={mapped}", flush=True)
                    # Diagnostics: query connection status and buffer frames
                    try:
                        info = TUCAM_VALUE_INFO()
                        info.nID = TUCAM_IDINFO.TUIDI_CONNECTSTATUS.value
                        ret = TUCAM_Dev_GetInfo(self.TUCAMOPEN.hIdxTUCam, pointer(info))
                        print(f"CONNECTSTATUS ret={ret} val={info.nValue}", flush=True)
                        info2 = TUCAM_VALUE_INFO()
                        info2.nID = TUCAM_IDINFO.TUIDI_CURRENTBUFFRAMES.value
                        ret2 = TUCAM_Dev_GetInfo(self.TUCAMOPEN.hIdxTUCam, pointer(info2))
                        print(f"CURRENTBUFFRAMES ret={ret2} val={info2.nValue}", flush=True)
                    except Exception as ex:
                        print(f"Diag exception: {ex}", flush=True)
        finally:
            print('Aborting waits...', flush=True)
            TUCAM_Buf_AbortWait(self.TUCAMOPEN.hIdxTUCam)
            print('Stopping capture...', flush=True)
            TUCAM_Cap_Stop(self.TUCAMOPEN.hIdxTUCam)
            print('Releasing buffer...', flush=True)
            TUCAM_Buf_Release(self.TUCAMOPEN.hIdxTUCam)

if __name__ == '__main__':
    demo = Tucam()
    try:
        demo.OpenCamera(0)
        if demo.TUCAMOPEN.hIdxTUCam != 0:
            demo.WaitForImageData()
        else:
            print('Camera handle is 0 after open. Skipping capture.', flush=True)
    finally:
        # Always attempt graceful shutdown
        try:
            demo.CloseCamera()
        except Exception as e:
            print(f"CloseCamera exception: {e}")
        demo.UnInitApi()
