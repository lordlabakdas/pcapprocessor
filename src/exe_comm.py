## -*- Mode:Python; -*- ##
##
## Copyright (c) 2018 ResiliNets, ITTC, University of Kansas
##
## Author: Siddharth Gangadhar
##
## James P.G. Sterbenz <jpgs@ittc.ku.edu>, director
## ResiliNets Research Group  http://wiki.ittc.ku.edu/resilinets
## Information and Telecommunication Technology Center (ITTC)
## and Department of Electrical Engineering and Computer Science
## The University of Kansas Lawrence, KS USA.
##

import subprocess
from subprocess import PIPE


def exe_comm(cmd):
    pipe = subprocess.Popen(cmd, stdout=PIPE)
    result, err = pipe.communicate()
    return result


def exe_com(cmd):
    pipe = subprocess.Popen(cmd, stdout=PIPE)
    for line in iter(pipe.stdout.readline, ""):
        print(line)
    pipe.communicate()
