import typing
import os
import dataclasses
from . import slottedDataClass


#@dataclasses.dataclass(slots=True)
@slottedDataClass.slottedDataClass(order=True, slots=True)
class FastaIndexLine:
    contig:str
    baseLength:int
    startByte:int
    lineBases:int
    lineBytes:int

    def __post_init__(self):
        self.baseLength = int(self.baseLength)
        self.startByte = int(self.startByte)
        self.lineBases = int(self.lineBases)
        self.lineBytes = int(self.lineBytes)

    @property
    def byteLength(self) -> int:
        totalLines = self.baseLength // self.lineBases
        lastLineLength = self.baseLength % self.lineBases
        totalBytesWithoutLastLine = totalLines * self.lineBytes
        totalBytesWithLastLine = totalBytesWithoutLastLine + lastLineLength # this will leave off any non-printing characters on the last line
        return totalBytesWithLastLine

    @property
    def picardString(self):
        picardString = "@SQ\tSN:%s\tLN:%s" % (self.contig, self.baseLength)
        return picardString


def processFaidxStream(faidxStream:typing.TextIO) -> typing.List[FastaIndexLine]:
    faidxList = []
    for line in faidxStream:
        line = line.strip()
        if not line:
            continue
        lineList = line.split("\t")
        contig, byteLength, startByte, lineBases, lineBytes = lineList
        faidxList.append(FastaIndexLine(contig, byteLength, startByte, lineBases, lineBytes))
    return faidxList


def readFastaIndexFile(path:str) -> typing.List[FastaIndexLine]:
    if not os.path.isfile(path):
        raise FileNotFoundError("Unable to find file %s" %path)
    file = open(path, 'r')
    faidxList = processFaidxStream(file)
    file.close()
    return faidxList
