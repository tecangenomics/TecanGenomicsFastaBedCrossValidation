import typing
import binascii
import gzip

def streamIsGzipped(dataStream:typing.IO[bytes]) -> bool:
    dataStream.seek(0)
    firstTwoBytes = dataStream.read(2)
    dataStream.seek(0)
    if not binascii.hexlify(firstTwoBytes) == b'1f8b':
        return False
    try:
        readTest = gzip.GzipFile(fileobj=dataStream)
        tenBytes = readTest.read(10) # I don't need the actual data here, just making sure that I can read it without throwing an exception.
    except OSError:
        dataStream.seek(0)
        return False
    dataStream.seek(0)
    return True


def fileIsGzipped(path:str) -> bool:
    fileHandle = open(path, 'rb')
    gzipped = streamIsGzipped(fileHandle)
    return gzipped