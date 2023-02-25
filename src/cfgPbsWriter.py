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


def cfgPbsWriter(configFile, jobsDir):
    emailID = "siddharth@ittc.ku.edu"
    work_dir = "/work/siddharth/ns-3/dce-Nov15/dce/source/ns-3-dce/"
    # tcpVariants = ["bic"]
    #    scenario = [configFile[:5]]
    scenario = configFile.split("_", 1)[0]
    # tcpVariants = ["bic", "cubic", "highspeed", "htcp", "hybla", "Illinois", "lp", "reno", "scalable", "westwood", "vegas", "yeah"]
    # scenario = ["error", "bandwidth", "bottleneckDelay", "bottleneckSpeed"]
    # driverFileName = "driver.sh"
    nodeSpecs = "#PBS -l nodes=1:ppn=2,mem=2000M,walltime=120:0:0"
    # jobsDir = "mul-flows-Jan15_11-18"
    cfgID = configFile[:-4]
    # print tcpVariants
    #############################################################################################################################################
    if not os.path.exists(jobsDir):
        os.makedirs(jobsDir)

    #    driverFileName = os.path.join(jobsDir, driverFileName) (change this behavior using *configFile)
    #    driverFile = open(driverFileName, "wb") (change this behavior using *configFile)

    for scen in scenario:
        # uniqueID = cfgName + "_" + tcp +  "_" + scen
        runDir = "/tmp/" + "tmp_" + cfgID
        runCmd = "python " + work_dir + "dceRunner.py " + configFile + " " + scenario
        pbsFiName = cfgID + ".pbs"
        pbsFileName = os.path.join(jobsDir, pbsFiName)
        clusterJobName = "#PBS -N " + cfgID + "\n"
        pbsFile = open(pbsFileName, "wb")
        pbsFile.write(nodeSpecs + "\n")
        pbsFile.write("#PBS -j oe" + "\n")
        pbsFile.write("#PBS -S /bin/sh" + "\n")
        pbsFile.write("#PBS -M " + emailID + "\n")
        pbsFile.write("#PBS -m a" + "\n")
        pbsFile.write(clusterJobName + "\n")
        pbsFile.write("cd $PBS_O_WORKDIR" + "\n")
        pbsFile.write("SAVE_LDLP=$LD_LIBRARY_PATH" + "\n")
        pbsFile.write("SAVE_DCE=$DCE_PATH" + "\n")
        pbsFile.write("SAVE_DCE_ROOT=$DCE_ROOT" + "\n")
        pbsFile.write(
            "export LD_LIBRARY_PATH=$SAVE_LDLP:`pwd`/../../build/lib:`pwd`/../../build/bin:`pwd`/build/bin:`pwd`/../../build/bin_dce:`pwd`/../../build/lib:`pwd`/../../build/bin:`pwd`/build/bin:`pwd`/../../build/bin_dce:`pwd`/build/lib:`pwd`/build/lib:`pwd`/build/bin:/panfs/pfs.acf.ku.edu/work/siddharth/ns-3/dce-Nov15/dce/build/lib:/panfs/pfs.acf.ku.edu/work/siddharth/ns-3/dce-Nov15/dce/build/bin"
            + "\n"
        )
        pbsFile.write(
            "export DCE_PATH=$SAVE_DCE:`pwd`/build/bin_dce:/panfs/pfs.acf.ku.edu/work/siddharth/ns-3/dce-Nov15/dce/build/sbin:/panfs/pfs.acf.ku.edu/work/siddharth/ns-3/dce-Nov15/dce/build/bin_dce:/usr/lib/gcc/x86_64-redhat-linux/4.4.6::`pwd`/../../build/lib:`pwd`/../../build/bin:`pwd`/build/bin:`pwd`/../../build/bin_dce:`pwd`/../../build/lib:`pwd`/../../build/bin:`pwd`/build/bin:`pwd`/../../build/bin_dce:`pwd`/build/lib:`pwd`/build/lib:`pwd`/build/bin:/panfs/pfs.acf.ku.edu/work/siddharth/ns-3/dce-Nov15/dce/build/lib:/panfs/pfs.acf.ku.edu/work/siddharth/ns-3/dce-Nov15/dce/build/bin"
            + "\n"
        )
        pbsFile.write(
            "export DCE_ROOT=$SAVE_DCE_ROOT:`pwd`/build:/panfs/pfs.acf.ku.edu/work/siddharth/ns-3/dce-Nov15/dce/build"
            + "\n"
        )
        pbsFile.write("cd " + work_dir + "\n")
        pbsFile.write("mkdir " + runDir + "\n")
        pbsFile.write("cp " + configFile + " " + runDir + "\n")
        pbsFile.write("cd " + runDir + "\n")
        pbsFile.write(
            "stdbuf -o L -e L "
            + runCmd
            + " | tee /projects/resilinets/siddharth/live-output_"
            + cfgID
            + ".$PBS_JOBID"
            + "\n"
        )
        pbsFile.write("mv *.csv *.mon " + work_dir + "\n")
        pbsFile.write("cd " + runDir + "\n")
        pbsFile.write("rm -rf " + runDir + "\n")
        #        pbsFile.write ("cd " + work_dir + jobsDir + "\n")
        #        pbsFile.write ("mkdir cfg csv logs mon pbs" + "\n")
        #        pbsFile.write ("mv ../*.cfg cfg" + "\n")
        #        pbsFile.write ("mv ../*.mon mon" + "\n")
        #        pbsFile.write ("mv ../*.csv csv" + "\n")
        #        pbsFile.write ("mv *.pbs pbs" + "\n")
        #        pbsFile.write ("mv *.sh pbs" + "\n")
        #        pbsFile.write ("mv ../*.o* logs" + "\n")
        pbsFile.close()
        # driverFile.write ("qsub " + pbsFiName + "\n") (change this behavior using *configFile)
    # driverFile.close () (change this behavior using *configFile)
