#########################################
# ExMerge.py
# .: Sample :.
# % python .\ExMerge.py -y 2000 -m 1 -Y 2001 -M 2 -i 3 -e good_password
# Author:
# - Timothy C. Quinn
#########################################

import pprint
import os
import shutil
import subprocess
import sys
import traceback
import time
import types
import json
import getopt
import logging

log = None
QDTSTAMP="%y%m%d-%H%M%S"

def printCli(s=None):
    print """runExMerge.py 
        [-y|--start_year] <start_year>
        [-m|--start_month] <start_month>
        [-Y|--end_year] <end_year>
        [-M|--end_month] <end_month>
        [-i|--interval] <interval>
        [[-e|--encrypt] <password>]
    """
    if not s is None:
        print s


def main(argv):
    global opts, doExport_FailCodes, log, pf
    global QDTSTAMP
    pp = pprint.PrettyPrinter(indent=1, width=80, depth=None, stream=None)
    pf = pp.pformat
    
    opts=Dict({
        "file_exm_ini_working": "_ExMerge_working.ini",
        "file_user_working": "_user_working.txt",
        "file_users_in": "users_in.txt"
    })

    doExport_FailCodes = Dict({
        "general": 0,
        "pst_too_big": 1
    })

    # Command Line Options
    try:
        goOpts, goArgs = getopt.getopt(argv,"hy:m:Y:M:i:e:",["start_year=","start_month=","end_year=","end_month=","interval=","encrypt="])
    except getopt.GetoptError, exc:
        printCli(exc)
        sys.exit(2)
    for opt, arg in goOpts:
        if opt == '-h':
            printCli()
            sys.exit()
        elif opt in ("-y", "--start_year"):
            opts.start_year = arg
        elif opt in ("-m", "--start_month"):
            opts.start_month = arg
        elif opt in ("-Y", "--end_year"):
            opts.end_year = arg
        elif opt in ("-M", "--end_month"):
            opts.end_month = arg
        elif opt in ("-i", "--interval"):
            opts.interval = arg
        elif opt in ("-e", "--encrypt"):
            opts.do_encrypt = True
            opts.encr_pass = arg
    # . Assert CLI opts and parse
    opts.start_year=assertIntArg('opts.start_year',opts.start_year)
    opts.start_month=assertIntArg('opts.start_month',opts.start_month)
    opts.end_year=assertIntArg('opts.end_year',opts.end_year)
    opts.end_month=assertIntArg('opts.end_month',opts.end_month)
    opts.interval=assertIntArg('opts.interval',opts.interval)
    # end Command Line Options
    

    # Read prefs.json
    conf=None
    try:
        with open('prefs.json') as data_file:
            conf = json.load(data_file)
    except:
        traceback.print_exc()
        e = sys.exc_info()[0]
        pl('Failed while loading preferneces')
        return;
        
    #pl('prefs:{0}'.format(pf(prefs));return;
    # . Assert prefs
    opts.exch_server = agetConf(conf,'exch_server')
    opts.dir_output = assertDir(agetConf(conf,'dir_output'))
    opts.dir_input = assertDir(agetConf(conf,'dir_input'))
    opts.temp_dir = assertDir(agetConf(conf,'temp_dir'))
    opts.file_exm_exe = assertFile(agetConf(conf,'file_exm_exe'))
    opts.ldap_base = agetConf(conf,'ldap_base')
    # end prefs.json
    
    pl("opts before run: {0}".format(pf(opts)))
    #sys.exit()
    
    # Logging
    log = logging.getLogger()
    
    consoleHandler = logging.StreamHandler()
    fileHandler = None
   
    log.addHandler(consoleHandler)
    
    # Load users to process
    aUsersAll = readFile_asList(opts.dir_input+'/'+opts.file_users_in)
    #pl("aUsersAll: {0}".format(pf(aUsersAll)))

            
    # Loop through users
    for sUser in aUsersAll:
        # Create output folder
        sPathOut=opts.dir_output+'/'+sUser
        if not os.path.exists(sPathOut):
            os.makedirs(sPathOut)
            
        sMachineST=getMachineDT()
        pl('Starting for user: '+sUser)
        
        logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] ["+sUser+"] %(message)s")
        consoleHandler.setFormatter(logFormatter)    
        
        # Create File logging on per user basis
        if not fileHandler is None:
            fileHandler.close()
            log.removeHandler(fileHandler)
        fileHandler = logging.FileHandler(filename='{0}/_exmpy_{1}.log'.format(sPathOut, sMachineST))
        fileHandler.setFormatter(logFormatter)
        log.addHandler(fileHandler)
            
        iYearFrom=-1
        iMonthFrom=-1
        
        iInterValCur=opts.interval
            
        # While loop to enable corrective re-trys of exports
        while True:
            if iYearFrom == -1:# first iteration
                iYearFrom=opts.start_year
                iMonthFrom=opts.start_month
            else:
                if iMonthTo == 12:
                    iYearFrom = iYearTo+1
                    iMonthFrom = 1
                else:
                    iYearFrom = iYearTo
                    iMonthFrom = iMonthTo+1
                
            iYearTo=iYearFrom+(iInterValCur-1)/12
            iMonthTo=iMonthFrom + ((iInterValCur-1) % 12)
            if iMonthTo > 12:
                iYearTo = iYearTo + 1
                iMonthTo = iMonthTo - 12
                
            if iYearTo > opts.end_year:
                iYearTo = opts.end_year
                iMonthTo = opts.end_month
            elif iYearTo == opts.end_year and iMonthTo > opts.end_month:
                iMonthTo = opts.end_month
                

            jRet = doExport(sUser, iYearFrom, iMonthFrom, iYearTo, iMonthTo)
            
            pl("doExport() Complete")
            
            if jRet.failed:
                if jRet.fail_reason == doExport_FailCodes.pst_too_big:
                    # dial interval down, reset and try again
                    if iInterValCur < 4:
                        iInterValCur=iInterValCur-1
                    else:
                        iInterValCur = int(iInterValCur * 0.75)
                    iYearTo=iYearFrom
                    iMonthTo=iMonthFrom-1
                    continue

                else:
                    # Program failed. Assume that doExport printed out fail reason
                    pl("Program failed. Exiting.")
                    return
                
            # Check if done and exit
            if iYearTo == opts.end_year and iMonthTo >= opts.end_month:
                #pl('Exiting (1): iYearTo: {0}, opts.end_year: {1}, iMonthTo: {2}, opts.end_month: {3}'.format(iYearTo,opts.end_year,iMonthTo,opts.end_month))
                break
            if iYearTo > opts.end_year:
                #pl('Exiting (2): iYearTo: {0}, opts.end_year: {1}, iMonthTo: {2}, opts.end_month: {3}'.format(iYearTo,opts.end_year,iMonthTo,opts.end_month))
                break
# end main
            
        
# doExport
# . Exports PSTs for given user
# . Main business logic for export
def doExport(sUser, iYearFrom, iMonthFrom, iYearTo, iMonthTo):
    global opts, doExport_FailCodes, log, pf

    pl('doExport called: sUser: {0}, iYearFrom: {1}, iMonthFrom: {2}, iYearTo: {3}, iMonthTo: {4}'.format(sUser, iYearFrom, iMonthFrom, iYearTo, iMonthTo))

    # Derrive end date to use in ExMerge
    if iMonthTo == 12:
        iMonthToExM = 1
        iYearToExM = iYearTo+1
    else:
        iMonthToExM = iMonthTo+1
        iYearToExM = iYearTo

    sPathOut = opts.dir_output+'/'+sUser
    
    # Update user_working file
    fTmp = open(opts.dir_input+'/'+opts.file_user_working,'w')
    fTmp.write(opts.ldap_base+sUser)
    fTmp.close()

    
    # Make file prefix
    sFilePrefix="{0}{1:02d}_{2}{3:02d}".format(iYearFrom, iMonthFrom, iYearTo,iMonthTo)
    #str(iYearFrom) + padZero(iMonthFrom) + '_' + str(iYearTo) + padZero(iMonthTo)
    
    # Create ini file
    #shutil.copyfile(opts.dir_input+'/'+opts.file_exm_base, opts.dir_input+'/'+opts.file_exm_ini_working)
    
    # Define file names
    sLogFileName = sFilePrefix+'_'+sUser+'.log'
    sPstFileName = sFilePrefix+'_'+sUser+'.pst'
    sZipFileName = sFilePrefix+'_'+sUser+'.pst.zip'
    
    # . Append working data to ExMerge ini file
    fINI = open(opts.dir_input+'/'+opts.file_exm_ini_working,'w')
    fINI.write("""[EXMERGE]
MergeAction =0
LoggingLevel =0
FoldersProcessed =2
DataImportMethod =1
ReplaceDataOnlyIfSourceItemIsMoreRecent =1
CopyUserData =1
CopyAssociatedFolderData =1
RenameSpecialFolders=1
    """)
    fINI.write('\nSourceServerName ='+opts.exch_server)
    fINI.write('\nFileContainingListOfMailboxes ={0}\\{1}'.format(posixToWin(opts.dir_input), opts.file_user_working))
    fINI.write('\nDataDirectoryName ='+posixToWin(opts.temp_dir))
    fINI.write('\nLogFileName ={0}\\{1}'.format(posixToWin(opts.temp_dir), sLogFileName))
    fINI.write('\nSelectMessageStartDate ={0:02d}/01/{1}   00:00:00'.format(iMonthFrom,iYearFrom))
    fINI.write('\nSelectMessageEndDate ={0:02d}/01/{1}   00:00:00'.format(iMonthToExM,iYearToExM))
    fINI.close()
    
    
    # Execute ExMerge
    spExM = subprocess.Popen([opts.file_exm_exe, "-F", posixToWin(opts.dir_input)+"\\"+opts.file_exm_ini_working, "-B", "-D"])
    fLog = None
    # . Sleep for a few secs but catch early finish
    for i in range(3):
        if not spExM.poll() is None:
            break;
        time.sleep(1)    

    # Start watching ExMerge
    while True:
    
        # Detect if ExMerge process is done
        rc=spExM.poll()
        if rc is None:# not done. sleep and continue watching
            pl("watching ExMerge - RC = None (still running)...")
            time.sleep(5)
        elif rc == 0:# done
            pl("watching ExMerge - RC = 0 (done)...")
            if not fLog is None:
                fLog.close()
            break
        else:# failed
            pl("watching ExMerge - RC = {1} (fail)...".format(rc))
            if not fLog is None:
                fLog.close()
            stdout, stderr = spExM.communicate()
            raise Exception("ExMerge failed with error code {0}. Message: {1} {2}. Check logs for more.".format(rc, stdout, stderr))
            
        # Lets check if we have hit 2gig limit
        iSize = os.path.getsize(opts.temp_dir+'/'+sUser+'.pst')
        if iSize > 2110000000:# then possible about to hit 2gig limit
            if fLog is None:
                fLog = open(opts.temp_dir+'/'+sLogFileName,'r')
            sLine=tail(fLog,1)
            #pl("aLine = {0}".format(sLine))
            
            # Search for MAPI_W_PARTIAL_COMPLETION in log file
            if sLine.find('MAPI_W_PARTIAL_COMPLETION') != -1:# 
                pl("watching ExMerge - Maxed out size...")
                # We have hit the 2gig limit. Abandon and start again
                fLog.close()
                # Kill ExMerge process
                spExM.kill()
                pl("sleeping before clean restart")

                # sleep to allow locks to be cleared
                time.sleep(10)

                # Delete working files
                os.remove(opts.temp_dir+'/'+sLogFileName)
                os.remove(opts.temp_dir+'/'+sUser+'.pst')

                # Send message to caller that export failed
                return Dict({"failed": True, "fail_reason": doExport_FailCodes.pst_too_big})




    # Assert that PST file exists
    if not os.path.isfile(opts.temp_dir+'/'+sUser+'.pst'):
        raise Exception('. ExMerge Did not fail but no PST found. '+'User = '+sUser+'. check log files.')

    # Rename PST file
    os.rename(opts.temp_dir+'/'+sUser+'.pst', opts.temp_dir+'/'+sPstFileName)
    
    
    
    if opts.do_encrypt:
        # Encrypt file
        subprocess.call([
            'C:/Program Files/7-Zip/7z', 'a', '-p'+opts.encr_pass, '-y', '-tzip', '-mx=0'
            , opts.temp_dir+'/'+sZipFileName
            , opts.temp_dir+'/'+sFilePrefix+'_'+sUser+'.pst'
            , opts.temp_dir+'/'+sFilePrefix+'_'+sUser+'.log'
        ])

        os.remove(opts.temp_dir+'/'+sPstFileName)
        
    # Now move files to final destination
    pl("Moving Files to final destination")
    shutil.move(opts.temp_dir+'/'+sLogFileName, sPathOut+'/'+sLogFileName)
    if opts.do_encrypt:
        shutil.move(opts.temp_dir+'/'+sZipFileName, sPathOut+'/'+sZipFileName)
    else:
        shutil.move(opts.temp_dir+'/'+sPstFileName, sPathOut+'/'+sPstFileName)
    pl("(done)")
    
    return Dict({"failed": False})
# end doExport



# Start helper code
def assertIntArg(sAlias,sVal):
    i=None
    try:
        i=int(sVal)
    except:
        raise Exception("Argument {0} is not an int. Got: {1}".format(sAlias,sVal))
    return i

def assertDir(sDir):
    if not os.path.exists(sDir):
        raise Exception("Directory not found: {0}".format(sDir))
    return sDir
    
def assertFile(sFile):
    if not os.path.exists(sFile):
        raise Exception("File not found: {0}".format(sFile))
    return sFile
    
def agetConf(conf,sName,bAllowBlank=True):
    ret=None
    try:
        ret=conf[sName]
    except:
        raise Exception('Missing preference {0}'.format(sName)) 
    if not isinstance(ret, basestring):
        raise Exception('preference {0} is not a string.'.format(sName)) 
    ret=ret.strip()
    if not bAllowBlank and ret == "":
        raise Exception('preference {0} must not be blank.'.format(sName)) 
    return ret
    
def posixToWin(sPPath):
    return sPPath.replace('/','\\')

def readFile_asList(sFileName):
    fIn = open(sFileName,'r')
    sRaw = fIn.read().replace("\r","").strip()
    aRet = sRaw.split('\n')
    return aRet

# Borrowed from StackOverflow
def tail(f, lines=20 ):
    total_lines_wanted = lines

    BLOCK_SIZE = 1024
    f.seek(0, 2)
    block_end_byte = f.tell()
    lines_to_go = total_lines_wanted
    block_number = -1
    blocks = [] # blocks of size BLOCK_SIZE, in reverse order starting
                # from the end of the file
    while lines_to_go > 0 and block_end_byte > 0:
        if (block_end_byte - BLOCK_SIZE > 0):
            # read the last block we haven't yet read
            f.seek(block_number*BLOCK_SIZE, 2)
            blocks.append(f.read(BLOCK_SIZE))
        else:
            # file too small, start from begining
            f.seek(0,0)
            # only read what was not read
            blocks.append(f.read(block_end_byte))
        lines_found = blocks[-1].count('\n')
        lines_to_go -= lines_found
        block_end_byte -= BLOCK_SIZE
        block_number -= 1
    all_read_text = ''.join(reversed(blocks))
    return '\n'.join(all_read_text.splitlines()[-total_lines_wanted:])

def pl(*args):
    global log
    if log is None:
        print("{0} - ".format(getMachineDT, (args[0] if len(args) == 1 else args[0].format(args[1:]))))
    else:
        log.warning(*args)

def getMachineDT():
    global QDTSTAMP
    return time.strftime(QDTSTAMP)

class Dict(dict):
    def __getattr__(self, attr):
        return self.get(attr)
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__
    
# End helper code
main(sys.argv[1:])
