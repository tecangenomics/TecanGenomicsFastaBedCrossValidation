import os
from . import gzipDetector
import subprocess


_SAMTOOLSPATH = ""


def setSamToolsPath(forcePath:str="", validatePath:bool=True) -> str:
    global _SAMTOOLSPATH
    commonSamtoolsPaths = [
        "/usr/bin/samtools",
        "/opt/conda/bin/samtools"
    ]
    if forcePath:
        _SAMTOOLSPATH = forcePath
    if not _SAMTOOLSPATH:
        try:
            whichSamtools = subprocess.Popen(["which" "samtools"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = whichSamtools.communicate()
            _SAMTOOLSPATH = stdout.decode().strip()
        except FileNotFoundError: # This should be hit if the system doesn't have the which command
            pass
    if not _SAMTOOLSPATH:
        for commonPath in commonSamtoolsPaths:
            if os.path.isfile(commonPath):
                _SAMTOOLSPATH = commonPath
                break
    if not _SAMTOOLSPATH:
        if validatePath:
            raise FileNotFoundError("Unable to find a Samtools executable.")
        else:
            print("WARNING: Unable to find a Samtools executable")
            return ""
    if not os.path.isfile(_SAMTOOLSPATH):
        if validatePath:
            raise FileNotFoundError("Unable to find expected Samtools executable at %s" % _SAMTOOLSPATH)
        else:
            print("WARNING: Unable to find expected Samtools executable at %s" % _SAMTOOLSPATH)
            return ""
    return _SAMTOOLSPATH


def indexFasta(inputFilePath:str, forceReindex:bool=False) -> str:
    if not os.path.isfile(inputFilePath):
        raise FileNotFoundError("Unable to find input file at %s" %inputFilePath)
    inputFolder, inputFileName = os.path.split(os.path.abspath(inputFilePath))
    outputFolder = inputFolder
    outputFileName = inputFileName + ".fai"
    outputFilePath = os.path.join(outputFolder, outputFileName)
    if os.path.isfile(outputFilePath):
        if not forceReindex:
            print("FASTA dictionary already exists at %s. Not set to reindex, so using existing file." %outputFilePath)
            return outputFilePath
    gzippedFile = gzipDetector.fileIsGzipped(inputFilePath)
    if gzippedFile:
        command = "gzip -dc %s | %s faidx --fai-idx %s -" %(inputFilePath, _SAMTOOLSPATH, outputFilePath)
        altCommand = "gzip -dc %s | %s faidx - && mv ./-.fai %s" %(inputFilePath, _SAMTOOLSPATH, outputFilePath) #Workaround for older versions of samtools that do not support naming the fasta index
    else:
        command = "%s faidx -o %s %s" %(_SAMTOOLSPATH, outputFilePath, inputFilePath)
    print("Running Fasta Index: " + command)
    returnCode = os.system(command)
    if gzippedFile and returnCode != 0:
        print("Initial attempt on gzipped file failed. Attempting workaround command.")
        returnCode = os.system(altCommand)
    if returnCode != 0:
        raise SamtoolsFailure("Samtools fasta index returned a non-zero exit status")
    else:
        return outputFilePath


def makeFastaDict(inputFilePath:str, forceReindex:bool=False) -> str:
    if not os.path.isfile(inputFilePath):
        raise FileNotFoundError("Unable to find input file at %s" %inputFilePath)
    inputFolder, inputFileName = os.path.split(os.path.abspath(inputFilePath))
    outputFolder = inputFolder
    outputFileName = inputFileName + ".dict"
    outputFilePath = os.path.join(outputFolder, outputFileName)
    if os.path.isfile(outputFilePath):
        if not forceReindex:
            print("FASTA dictionary already exists at %s. Not set to reindex, so using existing file." %outputFilePath)
            return outputFilePath
    if gzipDetector.fileIsGzipped(inputFilePath):
        command = "gzip -dc %s | %s dict -o %s -" % (inputFilePath, _SAMTOOLSPATH, outputFilePath)
    else:
        command = "%s dict -o %s %s" %(_SAMTOOLSPATH, outputFilePath, inputFilePath)
    print("Running Fasta Dictionary: " + command)
    returnCode = os.system(command)
    if returnCode != 0:
        raise SamtoolsFailure("Samtools fasta dict returned a non-zero exit status")
    else:
        return outputFilePath


class SamtoolsFailure(Exception):
    pass


setSamToolsPath(validatePath=False)