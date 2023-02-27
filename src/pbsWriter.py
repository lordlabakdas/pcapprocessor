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

import os


def pbsWriter(configFile):
    emailID = ""
    work_dir = ""
    tcpVariants = ["bic"]
    scenario = ["error"]
    driverFileName = "driver.sh"
    nodeSpecs = "#PBS -l nodes=1:ppn=2,mem=1000M"
    jobsDir = "initial-test"
    cfgName = configFile[:-4]

    #############################################################################################################################################
    if not os.path.exists(jobsDir):
        os.makedirs(jobsDir)

    driverFileName = os.path.join(jobsDir, driverFileName)
    driverFile = open(driverFileName, "wb")

    for tcp in tcpVariants:
        for scen in scenario:
            uniqueID = cfgName + "_" + tcp + "_" + scen
            runDir = "tmp_" + uniqueID
            runCmd = "python ../dceRunner.py " + configFile + " " + scen + " " + tcp
            pbsFiName = uniqueID + ".pbs"
            pbsFileName = os.path.join(jobsDir, pbsFiName)
            clusterJobName = "#PBS -N " + uniqueID + "\n"
            pbsFile = open(pbsFileName, "wb")
            pbsFile.write(nodeSpecs + "\n")
            pbsFile.write("#PBS -j oe" + "\n")
            pbsFile.write("#PBS -S /bin/sh" + "\n")
            pbsFile.write("#PBS -M " + emailID + "\n")
            pbsFile.write("#PBS -m abe" + "\n")
            pbsFile.write(clusterJobName + "\n")
            pbsFile.write("cd $PBS_O_WORKDIR" + "\n")
            pbsFile.write("SAVE_LDLP=$LD_LIBRARY_PATH" + "\n")
            pbsFile.write("SAVE_DCE=$DCE_PATH" + "\n")
            pbsFile.write(
                "export"
                " LD_LIBRARY_PATH=$SAVE_LDLP:`pwd`/../../../build/lib:`pwd`/../../../build/bin:`pwd`/../build/bin:`pwd`/../../../build/bin_dce"
                + "\n"
            )
            pbsFile.write(
                "export"
                " DCE_PATH=$SAVE_DCE:`pwd`/../build/bin_dce:`pwd`../../../../dce/build/sbin:`pwd`../../../../dce/build/bin_dce:`pwd`/../build/lib:`pwd`/../build/bin:`pwd`../../../../dce/build/lib:`pwd`../../../../dce/build/bin"
                + "\n"
            )
            pbsFile.write("cd " + work_dir + "\n")
            pbsFile.write("mkdir " + runDir + "\n")
            pbsFile.write("cp " + configFile + " " + runDir + "\n")
            pbsFile.write("cd " + runDir + "\n")
            pbsFile.write(runCmd + "\n")
            pbsFile.write("mv *.csv ../" + "\n")
            pbsFile.write("cd .." + "\n")
            pbsFile.write("rm -rf " + runDir + "\n")
            pbsFile.close()
            driverFile.write("qsub " + pbsFiName + "\n")
    driverFile.close()
