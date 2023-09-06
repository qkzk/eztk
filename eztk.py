#! /usr/bin/python

import os
from src.ui import EZView

# from src.ui import EZTKView

dirname = os.path.dirname(__file__)
logfile = os.path.join(dirname, "log/textual.log")

print("EZTK is starting...")
EZView().run()
# EZTKView().run()
