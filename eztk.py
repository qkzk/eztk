#! /usr/bin/python

import os
from src.ui import EZView

dirname = os.path.dirname(__file__)
logfile = os.path.join(dirname, "log/textual.log")

print("EZTK is starting...")
EZView().run()
