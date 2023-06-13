import typing
import os
import dataclasses
from . import slottedDataClass


VALIDBEDFORMATLENGTHS = [3, 4, 6, 12]

VALIDATIONRUN = False


#@dataclasses.dataclass(order=True, slots=True)
@slottedDataClass.slottedDataClass(order=True, slots=True)
class Interval:
    """Numbering should follow the BED standard of start being base zero and end being base 1 (AKA start position inclusive and end position noninclusive)"""

    sort_index: tuple = dataclasses.field(init=False, repr=False)
    contig: str
    _start: int
    _end: int
    _strand: str = "."
    errors:[list, None] = None

    def __post_init__(self):
        self.errors = []
        self.contig = str(self.contig)
        self._start = self.checkInt(self._start)
        self._end = self.checkInt(self._end)
        validatedStrandValue = self.checkStrandValue(self._strand)
        if not validatedStrandValue:
            message = "Valid strand values include +, -, and . only. %s is not a valid strand value." % self.strand
            if VALIDATIONRUN:
                self.errors.append(message)
            else:
                raise GenomicIntervalError(message)
        if not self.startValidRelativeToBase(self._start):
            message = "Start value of %s is less than zero" %self._start
            if VALIDATIONRUN:
                self.errors.append(message)
            else:
                raise GenomicIntervalError(message)
        self.validateStartAndEndRelativePositions(self._start, self._end)
        self.sort_index = (self.contig, self._start, self._end, self._strand)

    def validateStartAndEndRelativePositions(self, start: int, end: int):
        if end < start:
            message = "Given start value for interval of %s that was AFTER end value of %s" % (start, end)
            if VALIDATIONRUN:
                self.errors.append(message)
            else:
                raise GenomicIntervalError(message)
        if start == end:
            message =  "Start and end values of %s are equal, specifying an interval of no length." % start
            if VALIDATIONRUN:
                self.errors.append(message)
            else:
                raise GenomicIntervalError(message)

    def checkInt(self, value: int) -> int:
        try:
            return int(value)
        except ValueError:
            message = "%s was given where an integer belongs" % value
            if VALIDATIONRUN:
                self.errors.append(message)
            else:
                raise GenomicIntervalError(message)

    @staticmethod
    def startValidRelativeToBase(start: int) -> bool:
        if start < 0:
            return False
        return True

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value: int):
        start = self.checkInt(value)
        self.validateStartAndEndRelativePositions(start, self._end)
        if not self.startValidRelativeToBase(start):
            message = "Start value of %s is less than zero" % start
            if VALIDATIONRUN:
                self.errors.append(message)
            else:
                raise GenomicIntervalError(message)
        self._start = start

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value: int):
        end = self.checkInt(value)
        self.validateStartAndEndRelativePositions(self._start, end)
        self._end = end

    @staticmethod
    def checkStrandValue(strandValue:str) -> str:
        if strandValue == "+/-": # If you are going to use BED standard, please read the BED standard.
            strandValue = "." # It's a good standard and has served us well. These two lines hurt to write.
        if not strandValue in "+-.":
            return ""
        else:
            return strandValue

    @property
    def strand(self):
        return self._strand

    @strand.setter
    def strand(self, strandValue:str):
        validatedStrandValue = self.checkStrandValue(strandValue)
        if not validatedStrandValue:
            message = "Valid strand values include +, -, and . only. %s is not a valid strand value." %strandValue
            if VALIDATIONRUN:
                self.errors.append(message)
            else:
                raise GenomicIntervalError(message)
        self._strand = validatedStrandValue

    @property
    def lastIncludedBase(self) -> int:
        return self.end - 1

    def sameContig(self, other:'Interval') -> bool:
        return self.contig == other.contig

    def contains(self, other:'Interval') -> bool:
        return other in self

    def containedBy(self, other:'Interval') -> bool:
        return self in other

    def overlaps(self, other:'Interval') -> bool:
        if not self.sameContig(other):
            return False
        if other.lastIncludedBase < self.start:
            return False
        if self.lastIncludedBase < other.start:
            return False
        return True

    def __contains__(self, other:'Interval'):
        if not self.sameContig(other):
            return False
        return self.start <= other.start and self.lastIncludedBase >= other.lastIncludedBase

    @property
    def length(self) -> int:
        baseCount = self.end - self.start
        return baseCount

    def __str__(self):
        if self.strand in "+-":
            strand = self.strand
        else:
            strand = ""
        return "%s:%s-%s%s" %(self.contig, self.start, self.end, strand)

    def __len__(self):
        return self.length


class GenomicIntervalError(Exception):
    pass


#@dataclasses.dataclass(order=True, slots=True)
@slottedDataClass.slottedDataClass(order=True, slots=True)
class BEDLine:
    _bedFormatLength:int
    _contig:[str, int]
    _start:[str, int]
    _end:[str, int]
    name:str=""
    _score:[str, float]=None
    _strand:str="."
    thickStart:[str, int]=None
    thickEnd:[str, int]=None
    rgb:str=""
    blockCount:[str, int]=None
    blockSizes:str=""
    blockStarts:str=""
    interval:[None, Interval]=None
    thickInterval: [None, Interval] = None
    sort_index:[None, tuple] = None
    _errors:[None, list] = None

    def __post_init__(self):
        self._errors = []
        self._bedFormatLength = int(self._bedFormatLength)
        self.interval = Interval(self._contig, self._start, self._end, self._strand)
        self.name = str(self.name)
        self._score = self.processScore(self._score)
        if self.thickStart is not None and self.thickEnd is not None:
            self.thickInterval = Interval(self._contig, int(self.thickStart), int(self.thickEnd))
        else:
            self.thickInterval = None
        self.rgb = str(self.rgb)
        self.blockCount = self.processBlockCount(self.blockCount)
        self.sort_index = (self.interval, self.name)

    def processScore(self, score:[str, float, None]) -> [float, None]:
        if score is None:
            return None
        if score == ".":
            score = 0
        try:
            score = float(score)
        except ValueError:
            message = "Score value of %s does not appear to be a number." %score
            if VALIDATIONRUN:
                self._errors.append(message)
            else:
                raise BEDLineError(message)
        if type(score) in [float, int] and not 0 <= score <= 1000:
            message = "Score value was %s, but should be between 0 and 1000" %score
            if VALIDATIONRUN:
                self._errors.append(message)
            else:
                raise BEDLineError(message)
        return score

    def processBlockCount(self, blockCount:[str, int]) -> [int,  None]:
        if blockCount is None:
            return None
        try:
            blockCount = int(blockCount)
        except ValueError:
            message = "Block count value of %s does not appear to be an integer." %blockCount
            if VALIDATIONRUN:
                self._errors.append(message)
            else:
                raise BEDLineError(message)
        if blockCount < 0:
            message = "Block count value of %s is less than zero." %blockCount
            if VALIDATIONRUN:
                self._errors.append(message)
            else:
                raise BEDLineError(message)
        return blockCount

    @property
    def errors(self):
        errorList = []
        for error in self._errors:
            errorList.append(error)
        for error in self.interval.errors:
            errorList.append(error)
        if self.thickInterval:
            for error in self.thickInterval.errors:
                errorList.append("ThickInterval: " + error)
        return errorList

    @property
    def contig(self) -> str:
        return self.interval.contig

    @contig.setter
    def contig(self, contig:str):
        self.interval.contig = contig

    @property
    def start(self) -> int:
        return self.interval.start

    @start.setter
    def start(self, start:int):
        self.interval.start = start

    @property
    def end(self) -> int:
        return self.interval.end

    @end.setter
    def end(self, end:int):
        self.interval.end = end

    @property
    def strand(self) -> str:
        return self.interval.strand

    @strand.setter
    def strand(self, strand:str):
        self.interval.strand = strand

    @property
    def nameOrElse(self):
        if self._bedFormatLength > 3:
            return self.name
        else:
            createdName = "%s_%s_%s" %(self.contig, self.start, self.end)
            return createdName


class BEDLineError(Exception):
    pass


def processBEDStream(bedStream:typing.TextIO) -> typing.List[BEDLine]:
    bedLines = []
    bedFormat = None
    for line in bedStream:
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("browser"):
            continue
        if line.lower().startswith("track"):
            continue
        if line.startswith("#"):
            continue
        line = line.replace(" ", "\t")
        lineList = line.split("\t")
        lineLength = len(lineList)
        if bedFormat is None:
            bedFormat = lineLength
            if not bedFormat in VALIDBEDFORMATLENGTHS:
                raise BEDLineError("This file appears to be a BED with %s elements per line, but the only valid numbers of elements per line are %s" %(bedFormat, VALIDBEDFORMATLENGTHS))
        if lineLength != bedFormat:
            raise BEDLineError("This BED file appears to be a BED%s format, but length %s was seen on line %s" %(bedFormat,lineLength, line))
        try:
            bedLines.append(BEDLine(lineLength, *lineList))
        except Exception as error:
            raise BEDLineError("Trying to process the following line produced this error %s: %s   %s" %(type(error).__name__, error, line))
    if bedLines:
        return bedLines
    else:
        raise BEDLineError("Attempted to process BED data, but go no BED lines")


def readBEDFile(path:str) -> typing.List[BEDLine]:
    if not os.path.isfile(path):
        raise FileNotFoundError("Unable to find file %s" %path)
    file = open(path, 'r')
    bedLineList = processBEDStream(file)
    file.close()
    return bedLineList

