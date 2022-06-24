#! /usr/bin/python
import os
from src.ui import EZTKView

dirname = os.path.dirname(__file__)
logfile = os.path.join(dirname, "log/textual.log")

EZTKView().run(log=logfile)
