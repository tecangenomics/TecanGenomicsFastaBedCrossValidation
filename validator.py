import os
import sys
import typing
import traceback

try:
    from . import fbvsupport
except ImportError:
    import fbvsupport


TESTNAME = "FASTA and BED Validation"


def printHelp():
    print("USAGE: python3 validator.py <input.fasta> [<in1.bed> <in2.bed> <inN.bed>] <output.json>")
    print("This program requires an input FASTA and an output file to be specified. BED files are optional, but can include as many as needed to validate against the FASTA.")


def getFilePathsFromGUI() -> typing.List[str]:
    fileList = []
    fasta = fbvsupport.gui.selectFileForOpening("Select Reference Genome FASTA")
    if not fasta:
        raise ValueError("No FASTA reference genome was selected. Aborting analysis.")
    fileList.append(os.path.abspath(fasta))
    currentBED = True
    while currentBED:
        currentBED = fbvsupport.gui.selectFileForOpening("Select a BED file for analysis. Press CANCEL if all BED files have been selected.")
        if not currentBED:
            break
        fileList.append(os.path.abspath(currentBED))
    if not len(fileList) >= 2:
        raise ValueError("No BED files were selected to analyze. Aborting analysis.")
    outputFile = fbvsupport.gui.selectFileForSaving("Select validation report JSON output file.", defaultFileName="validationReport", defaultExtension="json")
    if not outputFile:
        raise ValueError("No output file selected. Aborting analysis.")
    fileList.append(os.path.abspath(outputFile))
    return fileList


class ArgPack:

    def __init__(self, fastaFile:str, bedFiles:typing.List[str], outputFile:str, skipValidation:bool=False, expectBedFiles:bool=True):
        self.fastaFile = fastaFile
        if not bedFiles:
            self.bedFiles = []
        else:
            self.bedFiles = bedFiles
        self.outputFile = outputFile
        if not skipValidation:
            if not self.validated(expectBedFiles):
                raise ArgumentValidationFailure("One or more arguments failed to validate")

    def validated(self, expectBedFiles:bool=True) -> bool:
        passed = True
        if not os.path.isfile(self.fastaFile):
            print("ERROR: Unable to find FASTA file at %s" %self.fastaFile)
            passed = False
        if not self.bedFiles and expectBedFiles:
            print("WARNING: No BED file paths provided")
        for bedFile in self.bedFiles:
            if not os.path.isfile(bedFile):
                print("ERROR: Unable to find BED file at %s" %bedFile)
                passed = False

        # The following block of checks are to prevent a user who forgot to include an output file path from accidentally overwriting a BED file by mistake
        bedEndings = [".bed", ".bed3", ".bed4", ".bed6", ".bed12"]
        for ending in bedEndings:
            if self.outputFile.lower().endswith(ending):
                raise ArgumentValidationFailure("Given output file path of %s appears to end with %s and looks like it wants to be a BED file. \
                This is not permitted here to avoid unintentional overwriting of a BED file when the intended output path was forgotten. \
                Is that what happened here?" %(self.outputFile, ending))
        if os.path.isfile(self.outputFile) and os.stat(self.outputFile).st_size != 0:
            try:
                testBed =fbvsupport.bedReader.readBEDFile(self.outputFile)
            except: # Using a generic exception here because this is expected to fail in some way
                pass
            else: # What I want to find is if I can read the output file as a BED without failures
                raise ArgumentValidationFailure("Given output file path of %s was able to be read as a BED file. \
                    This is not permitted here to avoid unintentional overwriting of a BED file when the intended output path was forgotten. \
                    Is that what happened here?" %self.outputFile)
        try:
            touchFile = open(self.outputFile, 'w+')
            touchFile.close()

        # This just does a routine check to make sure that the output file can be written to when done
        except Exception as error:
            errorType = type(error).__name__[1]
            print("ERROR: Unable to open output file for writing at %s. Check permissions? Error generated: %s: %s" %(self.outputFile, errorType, error))
            passed = False
        return passed

    @classmethod
    def fromArgv(cls):
        positionalArgs = sys.argv[1:]
        if not len(positionalArgs) >= 2 and fbvsupport.gui.active:
                positionalArgs = getFilePathsFromGUI()
        if not len(positionalArgs) >= 2:
                print("Insufficient arguments passed and no active GUI")
                printHelp()
                quit(1)
        fasta = positionalArgs[0]
        output = positionalArgs[-1]
        beds = positionalArgs[1: -1]
        return cls(fasta, beds, output)


class ArgumentValidationFailure(Exception):
    pass


def parseArgs() -> ArgPack:
    return ArgPack.fromArgv()


def validateFASTAAndBEDs(fastaPath:str, *bedPaths:str) -> fbvsupport.validationReport.ValidationReport:
    return fbvsupport.validations.generateValidationReport(fastaPath, *bedPaths)


def writeOutputFile(validationReport:fbvsupport.validationReport.ValidationReport, outputPath:str, indent:int=2) -> str:
    outputFile = open(outputPath, 'w')
    outputFile.write(validationReport.toJSON(indent))
    outputFile.close()
    return outputPath


class PointlessPlaceholderException(Exception):
    pass


if __name__ == "__main__":
    exitStatus = 0
    allOrNothingException = Exception
    try:
        args = parseArgs()
        validationReport = validateFASTAAndBEDs(args.fastaFile, *args.bedFiles)
        writeOutputFile(validationReport, args.outputFile)
        print(validationReport)
    except allOrNothingException as err:
        print("Encountered an unhandled error as follows:")
        traceback.print_exc()
        print(err)
        exitStatus = 1
    finally:
        if exitStatus == 0:
            message = "Run was completed successfully."
        else:
            message = "Run was not successful. Please see above for error."
        if getattr(sys, "frozen", False):
            input(message + "\nPress enter to quit")
        sys.exit(exitStatus)
