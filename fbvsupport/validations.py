import typing
import re
import os

import fbvsupport.fastaAnalysis
from . import faidxReader
from . import fastaDictReader
from . import bedReader
from . import samtoolsRunner
from . import validationReport
from . import versionInfo


bedReader.VALIDATIONRUN = True

_WHITESPACEREGEX = re.compile("\s")
_VALIDATIONREPORT = validationReport.ValidationReport("FASTA and BED Validation")


def detectCollisionsInList(inputList:list) -> dict:
    occurrenceCounterDict = {}
    for item in inputList:
        if not item in occurrenceCounterDict:
            occurrenceCounterDict[item] = 0
        occurrenceCounterDict[item] +=1
    collisions = {}
    for key, count in occurrenceCounterDict.items():
        if count > 1:
            collisions[key] = count
    return collisions


def simplifyName(name:str) -> str:
    name = name.lower()
    name = re.sub(_WHITESPACEREGEX, "", name)
    return name


def makeNamingErrorList(faidxData:typing.List[faidxReader.FastaIndexLine]) -> list:
    namingErrorList = []
    rawNames = []
    collapsedNames = []
    for faidxLine in faidxData:
        rawNames.append(faidxLine.contig)
        collapsedNames.append(simplifyName(faidxLine.contig))
    rawNameCollisions = detectCollisionsInList(rawNames)
    collapsedNameCollisions = detectCollisionsInList(collapsedNames)
    for name, count in rawNameCollisions.items():
        error = "Detected %s contigs with the name %s" %(count, name)
        namingErrorList.append(error)
    for name, count in collapsedNameCollisions.items():
        error = "Detected %s contigs with names similar to %s" %(count, name)
        namingErrorList.append(error)
    return namingErrorList


def checkForDuplicateContigs(fastaDictList:typing.List[fastaDictReader.FastaDictLine]) -> list:
    errorList = []
    contigHashTable = {}
    for line in fastaDictList:
        if not line.md5Hash in contigHashTable:
            contigHashTable[line.md5Hash] = []
        contigHashTable[line.md5Hash].append(line.contig)
    for hash, contigList in contigHashTable.items():
        if len(contigList) < 2:
            continue
        else:
            error = "Found %s contigs that likely have identical sequence: %s" %(len(contigList), contigList)
            errorList.append(error)
    return errorList


def checkForDuplicateBEDIntervalNames(bedList:typing.List[bedReader.BEDLine]):
    duplicatedNameList = []
    rawNameList = []
    simplifiedNameList = []
    for bedLine in bedList:
        rawNameList.append(bedLine.nameOrElse)
        simplifiedNameList.append(simplifyName(bedLine.nameOrElse))
    rawNameCollisions = detectCollisionsInList(rawNameList)
    collapsedNameCollisions = detectCollisionsInList(simplifiedNameList)
    for name, count in rawNameCollisions.items():
        error = "Detected %s BED intervals with the name %s" % (count, name)
        duplicatedNameList.append(error)
    for name, count in collapsedNameCollisions.items():
        error = "Detected %s BED intervals with names similar to %s" % (count, name)
        duplicatedNameList.append(error)
    return duplicatedNameList


def checkForDuplicatedIntervals(bedList:typing.List[bedReader.BEDLine]):
    errorList = []
    intervalList = []
    for bedLine in bedList:
        interval = (
            bedLine.contig,
            bedLine.interval.start,
            bedLine.interval.end
        )
        intervalList.append(interval)
    duplicateIntervals = detectCollisionsInList(intervalList)
    for interval, count in duplicateIntervals.items():
        contig, start, stop = interval
        error = "Detected the interval %s:%s-%s used %s times in the BED file." %(contig, start, stop, count)
        errorList.append(error)
    return errorList


def crosscheckBEDFile(bedList:typing.List[bedReader.BEDLine],
                      faidxData:typing.List[faidxReader.FastaIndexLine]) -> list:
    errorList = []
    contigLengthTable = {}
    for line in faidxData:
        contigLengthTable[line.contig] = line.baseLength
    for line in bedList:
        if not line.contig in contigLengthTable:
            error = "BED line %s tried to reference contig %s which does not exist in the FASTA file." %(line.name, line.contig)
            errorList.append(error)
            continue
        if line.interval.lastIncludedBase > contigLengthTable[line.contig]:
            error = "BED line %s is trying to read interval %s which is out of its contig's bounds" %(line.name, line.interval)
            errorList.append(error)
    return errorList


def prependFileNameToErrorLines(fileName:str, errorList:typing.List[str]) -> typing.List[str]:
    if not errorList:
        return errorList
    errorList = [fileName + ": " + error for error in errorList]
    return errorList


def makeFaidx(fastaPath:str) -> str:
    try:
        faidxPath = samtoolsRunner.indexFasta(fastaPath)
    except samtoolsRunner.SamtoolsFailure:
        return ""
    return faidxPath


def makeFastaDictionary(fastaPath:str) -> str:
    try:
        fastaDictPath = samtoolsRunner.makeFastaDict(fastaPath)
    except samtoolsRunner.SamtoolsFailure:
        return ""
    return fastaDictPath


def validateFASTA(faidx:typing.List[faidxReader.FastaIndexLine], fastaDict:typing.List[fastaDictReader.FastaDictLine]) -> list:
    errorList = []
    namingErrors = makeNamingErrorList(faidx)
    duplicateContigs = checkForDuplicateContigs(fastaDict)
    errorList += namingErrors
    errorList += duplicateContigs
    return errorList


def validateBED(bedList:typing.List[bedReader.BEDLine]) -> list:
    errorList = []
    for lineNumber, line in enumerate(bedList):
        if line.errors:
            for error in line.errors:
                errorMessage = "Line %s: %s" %(lineNumber + 1, error)
                errorList.append(errorMessage)
    duplicateIntervalNames = checkForDuplicateBEDIntervalNames(bedList)
    duplicateIntervals = checkForDuplicatedIntervals(bedList)
    errorList += duplicateIntervalNames
    errorList += duplicateIntervals
    return errorList


def generateValidationReport(fastaPath:str, *bedPaths:str, verbose:bool=True) -> validationReport.ValidationReport:
    print("Tecan Genomics FASTA and BED cross validator | Version: %s | Date: %s" % (versionInfo.VERSION, versionInfo.DATE))
    _VALIDATIONREPORT.addInput("FASTA", fastaPath)
    for bedPath in bedPaths:
        _VALIDATIONREPORT.addInput("BED", bedPath)
    if not os.path.isfile(fastaPath):
        _VALIDATIONREPORT.addCritical("Unable to find FASTA file at %s" %fastaPath)
    for bedPath in bedPaths:
        if not os.path.isfile(bedPath):
            _VALIDATIONREPORT.addCritical("Unable to find BED file at %s" %bedPath)
    if not _VALIDATIONREPORT.passed:
        _VALIDATIONREPORT.addCritical("Stopping before further analysis due to the absence of expected files")
        return _VALIDATIONREPORT
    if samtoolsRunner._SAMTOOLSPATH:
        faidxPath = makeFaidx(fastaPath)
        if not faidxPath:
            _VALIDATIONREPORT.addCritical("Unable to index FASTA file at %s" %fastaPath)
        fastaDictPath = makeFastaDictionary(fastaPath)
        if not fastaDictPath:
            _VALIDATIONREPORT.addCritical("Unable to make a dictionary from FASTA file at %s" %fastaPath)
        if not _VALIDATIONREPORT.passed:
            _VALIDATIONREPORT.addCritical("Stopping before further analysis due to a corrupt or unreadable FASTA file at %s" %fastaPath)
            return _VALIDATIONREPORT
        if verbose:
            print("Initial processing of FASTA file was successful. Starting validations.")
        faidx = faidxReader.readFastaIndexFile(faidxPath)
        fastaDict = fastaDictReader.readFastaDictFile(fastaDictPath)
    else:
        print("Unable to find local Samtools installation. Analyzing FASTA with local packages.")
        try:
            faidx, fastaDict = fbvsupport.fastaAnalysis.analyzeFasta(fastaPath)
        except Exception as err:
            print("Error analyzing FASTA file at %s" %fastaPath)
            print(err)
            _VALIDATIONREPORT.addCritical("Stopping before further analysis due to a corrupt or unanalyzable FASTA file at %s" %fastaPath)
            return _VALIDATIONREPORT
    bedDict = {}
    for bedPath in bedPaths:
        try:
            bedDict[bedPath] = bedReader.readBEDFile(bedPath)
        except bedReader.BEDLineError as error:
            _VALIDATIONREPORT.addCritical("%s reading failed: %s" %(bedPath, error))
    fastaErrors = validateFASTA(faidx, fastaDict)
    fastaErrors = prependFileNameToErrorLines(fastaPath, fastaErrors)
    _VALIDATIONREPORT.addErrors(fastaErrors)
    for bedFilePath, bedLines in bedDict.items():
        bedFileErrors = validateBED(bedLines)
        bedFileCrosscheckErrors = crosscheckBEDFile(bedLines, faidx)
        bedFileErrors = prependFileNameToErrorLines(bedFilePath, bedFileErrors)
        bedFileCrosscheckErrors = prependFileNameToErrorLines(bedFilePath, bedFileCrosscheckErrors)
        _VALIDATIONREPORT.addErrors(bedFileErrors)
        _VALIDATIONREPORT.addErrors(bedFileCrosscheckErrors)
    return _VALIDATIONREPORT
