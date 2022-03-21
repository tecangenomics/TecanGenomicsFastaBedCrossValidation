import typing
import os
import dataclasses
from . import slottedDataClass


#@dataclasses.dataclass(slots=True)
@slottedDataClass.slottedDataClass(slots=True)
class FastaDictLine:

    contig:str
    byteLength:int
    md5Hash:str
    uri:str

    def __post_init__(self):
        self.byteLength = int(self.byteLength)


def stripDictFieldPrefix(value:str) -> str:
    return value[3:]


def processDictStream(dictStream:typing.TextIO) -> typing.List[FastaDictLine]:
    dictList = []
    for line in dictStream:
        line = line.strip()
        if not line:
            continue
        if not line.startswith("@SQ"):
            continue
        lineList = line.split("\t")
        lineList = [stripDictFieldPrefix(item) for item in lineList[1:]]
        if len(lineList) == 3:
            lineList.append("")
        contig, byteLength, md5Hash, uri  = lineList
        dictList.append(FastaDictLine(contig, byteLength, md5Hash, uri))
    return dictList


def readFastaDictFile(path:str) -> typing.List[FastaDictLine]:
    if not os.path.isfile(path):
        raise FileNotFoundError("Unable to find file %s" %path)
    file = open(path, 'r')
    fastaDictList = processDictStream(file)
    file.close()
    return fastaDictList