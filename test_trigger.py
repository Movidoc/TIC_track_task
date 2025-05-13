import numpy as np # conda install -k -c conda-forge numpy
import pygame as pg
import serial #conda install -k -c conda-forge pyserial

try: 
    from psychopy import parallel #conda install -k -c conda-forge psychopy
    PORT_ADDRESS = 0xdff8 # Port address for parallel port (LPT1) /Confirm with Device Manager
    _port = parallel.ParallelPort(PORT_ADDRESS) # initialise the port once
    _port.setData(0) # keeps lines low at launch
    HAVE_PARALLEL = True
    print("[trigger] LPT initialised at 0x{:X}".format(PORT_ADDRESS))
except Exception as e:
    _port = None
    HAVE_PARALLEL = False
    print("[trigger] No parallel port available – running without hardware triggers\n", e)
    print("          (error was:", e, ")")
    

def send_trigger(code: int, pulse_ms: int = 5):
   
   
    """
    code : 1‑255 → Brain Recorder writes the same S‑number
    """
    _port.setData(code)        # rising edge
    pg.time.wait(pulse_ms)
    _port.setData(0)           # falling edge
    pg.time.wait(2)
    print(f"[trigger] Sent {code}")

for n in (1, 2, 3, 4, 5):
    send_trigger(n)
    pg.time.wait(100) 

