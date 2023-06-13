from . import faidxReader
from . import fastaDictReader
import os
import typing
import hashlib
import pathlib


def extractContigFromLine(line: str):
    line = line.strip()
    if not line.startswith(">"):
        raise ValueError("Contig line should start with a '>', but passed line was: %s" % line)
    return line[1:].split()[0]


def analyzeFasta(path:str) -> typing.Tuple[typing.List[faidxReader.FastaIndexLine], typing.List[fastaDictReader.FastaDictLine]]:
    if not os.path.isfile(path):
        raise FileNotFoundError("Unable to find file %s" %path)
    fileURI = pathlib.Path(os.path.abspath(path)).as_uri()
    fastaIndexList = []
    fastaDictList = []
    fasta = open(path, 'r')
    firstLine = fasta.readline().strip()
    if not firstLine.startswith(">"):
        raise ValueError("First FASTA line should start with a '>' character. First line: %s" %firstLine)
    firstContig = extractContigFromLine(firstLine)
    if not firstContig:
        raise ValueError("Unable to extract first contig from first FASTA line. First line: %s" %firstLine)
    fasta.seek(0)
    startingFile = True
    newContig = False
    contig = ""
    baseLength = 0
    startByte = 0
    lineBases = 0
    lineBytes = 0
    byteLength = 0
    md5Hash = hashlib.md5("".encode())
    lastLineInconsistent = False
    line = fasta.readline()
    while line:
        if not line.strip():
            line = fasta.readline()
            continue
        if line.startswith(">"):
            if not startingFile:
                fastaIndexList.append(faidxReader.FastaIndexLine(contig, baseLength, startByte, lineBases, lineBytes))
                fastaDictList.append(fastaDictReader.FastaDictLine(contig, byteLength, md5Hash.hexdigest(), fileURI))
            startingFile = False
            newContig = True
            contig = extractContigFromLine(line)
            baseLength = 0
            startByte = fasta.tell()
            lineBases = 0
            lineBytes = 0
            byteLength = 0
            md5Hash = hashlib.md5("".encode())
            line = fasta.readline()
            lastLineInconsistent = False
            continue
        else:
            if lastLineInconsistent:
                raise ValueError("Found inconsistent line lengths in contig %s" %contig)
            currentLineBytes = len(line)
            line = line.strip()
            currentLineBases = len(line)
            if newContig:
                lineBytes = currentLineBytes
                lineBases = currentLineBases
            else:
                if currentLineBases != lineBases or  currentLineBytes != lineBytes:
                    lastLineInconsistent = True
            newContig = False
            baseLength += lineBases
            byteLength += lineBytes
            md5Hash.update(line.encode())
            line = fasta.readline()
    fasta.close()
    fastaIndexList.append(faidxReader.FastaIndexLine(contig, baseLength, startByte, lineBases, lineBytes))
    fastaDictList.append(fastaDictReader.FastaDictLine(contig, byteLength, md5Hash.hexdigest(), fileURI))
    return fastaIndexList, fastaDictList
