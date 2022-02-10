# Tecan Genomics FASTA and BED Cross-validation System

This program will perform the following validations on FASTA and BED files:
- FASTA Validations
  - Ensure that a FASTA index and dictionary can be created for the FASTA file
  - Check for duplicated contig names
  - Check for very similar contig names
    - Very similar names here means names that differ only by whitespace and/or capitalization
  - Check for contigs of identical sequence
- BED Validations
  - Identify lines not conforming to the BED standard in some manner
  - Identify duplicated interval names (if using BED6 or higher)
  - Identify very similar interval names (if using BED6 or higher)
    - Similar names, like above, indicate a difference of only capitalization and/or whitespace
- BED/FASTA cross-validations
  - Identify BED lines that reference a contig not present in the FASTA
  - Identify intervals that are outside the bounds of their contig

## Quick Start Guide

#### Command line

This program uses positional arguments where the first argument will always be the FASTA file being validated and the last argument will be the path for the detailed validation report (in JSON format).  Between the FASTA and report paths can be any number of BED files to be cross validated against the FASTA file.
```
python3 validator.py fastaFile.fa targets1.bed targets2.bed validationReport.json
python3 validator.py [FASTA] <BED1> <BED2> <BEDn> [output.json]
```
Note that writing the JSON validation report to a file ending in .bed is disallowed by this program.  This prevents potential errors caused by forgetting to include an output file path and instead overwriting your bed file.

#### Docker
This can be run inside a container and a Dockerfile is included to facilitate that.  The container includes all dependencies already installed at build time.  There are multiple methods that can be used to run this within its container depending upon the level of interaction/automation needed and the configuration of the host system.


#### As an import
You can also run validation as an imported library (useful if you want to call it from a Jupyter notebook).  To do this, first you will need to copy the package to a location where your Python interpreter can find it (try the current working directory or some location specified in your system's PYTHONPATH environment variable).  Once that is done you will need to import the package (assumed to be in a folder called bedFastaValidation below), and then call **validateFASTAAndBEDs** to generate the validation report.  This function requires the FASTA file to be the first parameter and can then take any number of BED files as parameters after the FASTA.  See below for an example:
```
import bedFastaValidation
validationReport = bedFastaValidation.validateFASTAAndBEDs("path/to/myFastaFile.fa", "path/to/bed1.bed", "path/to/bed2.bed")
```
Running this will generate a **ValidationReport** object with the following properties:
- criticalList (list): A list of critical issues, likely resulting in a file being unread due to serious formatting problems
- errorList (list): Detected errors in the supplied files
- warningList (list): Warnings about potential issues with the files
- noWarnings (bool): Returns true if warningList is empty, false otherwise
- noErrors (bool): Returns true if errorList and criticalList are both empty, false otherwise
- warningCount (int): Returns the number of warnings
- errorCount (int): Returns the number of errors and critical errors
- inputs (dict): Returns a dictionary identifying the input files supplied
- passed (bool): Returns true if no errors or warnings were given
- toDict() (dict): Returns a Python dictionary with the validation report details 
- toJSON(indent:int=2) (str): Returns a JSON-encoded version of the dictionary created by the toDict() method.  Indent value indicates how much indentation to use in the JSON string.  Keeping some indentation will make it more readable to humans while removing indentation will make it hard for humans to read, but more efficient on space.
- dumpToLogger(logger:logging.Logger) (None): This will output the report via the Python logger passed in as the parameter for the method
- Printing a ValidationReport object or otherwise calling it as a string will generate a short report string indicating whether or not it passed and how many errors and warnings were generated.  Additionally, if critical errors were observed, that will be indicated.

### Prerequisites

Prerequisites for running this program outside its container are relatively simple
- Python interpreter
  - Version 3.7 or newer is required
  - Version 3.10 is recommended as this program can leverage some new features to improve performance significantly
- Samtools available on the command line
  - This program will attempt to find the executable itself

## Versioning

Once this software is out of initial development and in release, we will use a modification of [Semantic Versioning](https://semvar.org) to identify our releases.

Release identifiers will be *major.minor.patch*

Major release: Newly required parameter or other change that is not entirely backwards compatible
Minor release: New optional parameter
Patch release: No changes to parameters

## License

This project is licensed under the GNU GPLv3 License - see the [LICENSE](LICENSE) file for details.
This license restricts the usage of this application for non-open sourced systems. Please contact the authors for questions related to relicensing of this software in non-open sourced systems.
