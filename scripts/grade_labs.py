#!/usr/bin/env python
#
# University of California, Santa Barbara
# Computer Science
# 
# CS16
# This script grabs a directory from the TURNIN dir
# and it uncompresses all the work turned in by the students
# into another output directory usually assigned as an argument.
#
# Victor Fragoso <vfragoso@cs.ucsb.edu>
# 02/11/10
# Stripped single quotes from names (i.e. "O'Conner") to keep shell cmd
# calls from bombing.
# Jasen Hall <jasen@cs.ucsb.edu>
# 11/5/13
#
# Last Mod: 11/5/13
# WARNING: Absolute no WARRANTY of this script. Sorry for the inconvinience
#

import sys
import re
import os
import glob
import subprocess

#Configuration File
CONF_FILE_NAME = 'conf.txt'

#PROPERTIES in ConfFile
CLASS_HOME='class.home'
TURNIN_DIR='turnin.dir'
WORK_DIR='work.dir'
WORK_POSTFIX='work.dir.postfix'
TURNIN_FEXT='turnin.fext'

#Simple Logger Property
LOGGER_STATUS='logger.debug'

#Arguments from Command Line
TA_ID='taid'
LAB_DIR='labdir'

#Info extracted from students
LAST_SUBMIT='last_submit'
STUDENTS_NAME='students_name'

#File Handling
INPUT_PATH='input'
OUTPUT_PATH='output'

############################################

def getStudentsName( args, uid ):
    finger_cmd = [r'finger', '-lm', uid]
    
    if args[LOGGER_STATUS]:
        print "[DEBUG] Invoking Command: finger -lm", uid

    out = subprocess.Popen(finger_cmd, stdout=subprocess.PIPE).communicate()[0]
    rexp = r'Login: .*Name: (.*).*'
    r = re.compile(rexp)

    m = r.match( out )
    stdname = str()
    if m:
        stdname = m.group(1).strip().replace(' ', '_')
	stdname = stdname.replace("'", "");  # quote breaks shell cmd calls
        if args[LOGGER_STATUS]:
            print "[DEBUG] Student's Name: ", stdname
        args[STUDENTS_NAME] = stdname.strip()
    else:
        print "[FATAL] Finger Error "

    return stdname

def getLastTurnin(listOfFiles, args):
    #Get the last TURNIN
    
    students_data = dict()

    for lab in listOfFiles:
        lab = lab.replace(args[INPUT_PATH]+'/', '')
        lab = lab.replace(args[TURNIN_FEXT],'')

        uid = lab
        pos = lab.rfind("-") 
        num = 0
        if pos != -1: 
            uid = lab[:pos]
            num = lab[pos + 1: ]

        if uid not in students_data: 
            students_data[uid] = dict()
            students_data[uid][LAST_SUBMIT]  = num
            students_data[uid][STUDENTS_NAME]= getStudentsName( args, uid )

        students_data[uid][LAST_SUBMIT] = max(num, students_data[uid][LAST_SUBMIT])

    #Dumping Students Info
    if args[LOGGER_STATUS]: print "[DEBUG] Student's Data :: ", str(students_data)

    return students_data

def extractList(args):
    if args[WORK_DIR] == 'nil': args[WORK_DIR] = ''

    #Building Paths
    inputPath  = os.path.join(args[CLASS_HOME], args[TURNIN_DIR])
    inputPath  = os.path.join(inputPath, args[LAB_DIR] )

    outputPath = os.path.join(args[CLASS_HOME], args[WORK_DIR])
    outputPath = os.path.join(outputPath, args[TA_ID])

    if args[WORK_POSTFIX]:
        outputPath = outputPath + args[WORK_POSTFIX]

    if args[LOGGER_STATUS]:
        print '[DEBUG] InputPath: ', inputPath
        print '[DEBUG] OutputPath: ', outputPath

    args[INPUT_PATH] = inputPath
    args[OUTPUT_PATH]= outputPath

    filterFileStr = '*' + args[TURNIN_FEXT]
    listInputPath = glob.glob( os.path.join(inputPath, filterFileStr) )

    students_data = getLastTurnin( list(listInputPath), args )

    return students_data

def extractInformation(stdnt_dir, uid, students_data, args):
    fileName = uid
    if students_data[uid][LAST_SUBMIT] != 0:
        fileName += '-' + students_data[uid][LAST_SUBMIT]

    fileName += args[TURNIN_FEXT]

    if args[LOGGER_STATUS]:
        print '[DEBUG] File Name to extract: ', fileName

    fileName = os.path.join(args[INPUT_PATH], fileName)

    cmd  = 'cd ' + stdnt_dir 
    cmd += '; zcat ' + fileName + ' | tar xvBf - > /dev/null'

    if args[LOGGER_STATUS]:
        print '[DEBUG] Invoking : ', cmd

    subprocess.Popen(cmd, shell=True).wait()

def uncompressLabs(args, students_data):
    #Verifying that TA has its own directory for grading
    if os.access(args[OUTPUT_PATH], os.F_OK):
        if args[LOGGER_STATUS]: print "[DEBUG] Output Path Exists!"
    else:
        print "[INFO] Creating OutputPath ... ", args[OUTPUT_PATH]
        os.mkdir(args[OUTPUT_PATH])

    #Create directory for each HW
    output_labdir = os.path.join(args[OUTPUT_PATH], args[LAB_DIR])
    if os.access(output_labdir, os.F_OK):
        print "[DEBUG] LabDir exist"
    else:
        print "[DEBUG] Creating Lab Directory ... ", output_labdir
        os.mkdir(output_labdir)

    #Uncompress 
    for uid in students_data:
        if args[LOGGER_STATUS]:
            print "[DEBUG] Uncompressing Lab for ", uid

        stdnt_dir = students_data[uid][STUDENTS_NAME]
        if stdnt_dir == '':
            print "[WARNING] Student's Name is empty using UCSB Net Id: ", uid
            stdnt_dir = uid

        stdnt_dir = os.path.join(output_labdir, stdnt_dir)

        #Creating Directory only if it doesn't exist
        if not os.access(stdnt_dir, os.F_OK):
            if args[LOGGER_STATUS]:
                print "[DEBUG] Creating Directory ", stdnt_dir

            os.mkdir(stdnt_dir)

        #Uncompressing the Tarball
        extractInformation(stdnt_dir, uid, students_data, args)

    return

##
#Parse the Conf File
def parseConfFile():
    confFile = open(CONF_FILE_NAME, 'r')

    reg_exp = r'(.*)=(.*)'
    r = re.compile(reg_exp)

    ##
    #Dictionary containing info from conffile
    conf = dict()
    
    #Reading file
    for line in confFile:
        line.strip()
        if line.find('#') != -1: continue #Comments
        
        match = r.match( line )

        if len( match.groups() ) == 0:
            print "[ERROR] Invalid Configuration File"

        if match.group(1) == CLASS_HOME:
            conf[CLASS_HOME] = match.group(2)
        elif match.group(1) == TURNIN_DIR:
            conf[TURNIN_DIR] = match.group(2)
        elif match.group(1) == WORK_DIR:
            conf[WORK_DIR]   = match.group(2)
        elif match.group(1) == TURNIN_FEXT:
            conf[TURNIN_FEXT]= match.group(2)
        elif match.group(1) == WORK_POSTFIX:
            if match.group(2) != 'nil':
                conf[WORK_POSTFIX]= match.group(2)
            else:
                conf[WORK_POSTFIX]= ''
        elif match.group(1) == LOGGER_STATUS:
            if match.group(2) != '1':
                conf[LOGGER_STATUS]= 0
            else:
                conf[LOGGER_STATUS]= 1
        else:
            print "[ERROR] Invalid Property in Conf File"
            return 
        
    confFile.close()

    if CLASS_HOME not in conf.keys():
        print "[ERROR] Invalid configuration file"
    elif TURNIN_DIR not in conf.keys():
        print "[ERROR] Invalid configuration file"
    elif WORK_DIR not in conf.keys():
        print "[ERROR] Invalid configuration file"
    elif TURNIN_FEXT not in conf.keys():
        print "[ERROR] Invalid configuration file"

    #Dump configuration properties
    if conf[LOGGER_STATUS]:
        print "[DEBUG] Configuration Properties : ", str(conf)

    return conf

##
#Entry Point
def main(argv):
    if len(sys.argv) != 3:
        print 'UCSB :: GradeLab Script'
        print '\tUsage: ./grade_labs.py <TAusername> <DirectoryToProcess>'
        print '\tTAusername ::= TA\'s Identifier'
        print '\tDirectoryToProcess ::= In other words lab dir to uncompress\n\n'
        print 'NOTE: This script reads a CONF file where it is specified the'
        print 'TURNIN directory. This conf.txt file should be in the same '
        print 'directory where this script resides'
        return

    ##
    #Reading CONF file
    args = parseConfFile()
    if not args: return

    ##
    #Read TURNIN/<directoryToProcess> and keep with the most updated submissions
    args[TA_ID]  = sys.argv[1]
    args[LAB_DIR]= sys.argv[2]

    ##
    #Extract list of files
    print "[INFO] Reading turned in labs ..."
    students_data = extractList(args)

    ##
    #Processing Directory
    print "[INFO] Uncompressing last submissions ..."
    uncompressLabs( args, students_data )

#
# Python entrypoint
if __name__=='__main__':
    main(sys.argv)
