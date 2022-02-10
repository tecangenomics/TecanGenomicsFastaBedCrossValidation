import json
import typing
import logging


class ValidationReport:

    def __init__(self, testName:str, criticalList:list=None, errorList:list=None, warningList:list=None):
        self.testName = testName
        if criticalList is None:
            self.criticalList = []
        else:
            self.criticalList = criticalList.copy()
        if errorList is None:
            self.errorList = []
        else:
            self.errorList = errorList.copy()
        if warningList is None:
            self.warningList = []
        else:
            self.warningList = warningList.copy()
        self._inputs = {}

    @property
    def noErrors(self) -> bool:
        if self.errorList or self.criticalList:
            return False
        else:
            return True

    @property
    def noWarnings(self) -> bool:
        if self.warningList:
            return False
        else:
            return True

    @property
    def warningCount(self) -> int:
        return len(self.warningList)

    @property
    def errorCount(self) -> int:
        return len(self.errorList) + len(self.criticalList)

    @property
    def inputs(self) -> dict:
        return self._inputs.copy()

    @property
    def passed(self) -> bool:
        return self.noWarnings and self.noErrors

    def addInput(self, name:str, value) -> None:
        if name not in self._inputs:
            self._inputs[name] = []
        try:
            self._inputs[name].append(value.copy())
        except: # Using a general exception here because this is expected to error in many cases and we have a fallback
            self._inputs[name].append(value)

    def addWarning(self, warning:str) -> None:
        self.warningList.append(warning)

    def addError(self, error:str) -> None:
        self.errorList.append(error)

    def addCritical(self, criticalError:str) -> None:
        self.criticalList.append(criticalError)
    
    def addWarnings(self, warnings:typing.List[str]) -> None:
        if type(warnings) == str:
            raise ValueError("The addWarnings method should only be run on a list. To add a string, run the addWarning method")
        for warning in warnings:
            self.warningList.append(warning)
            
    def addErrors(self, errors:typing.List[str]) -> None:
        if type(errors) == str:
            raise ValueError("The addErrors method should only be run on a list. To add a string, run the addError method")
        for error in errors:
            self.errorList.append(error)
            
    def addCriticals(self, criticals:typing.List[str]) -> None: # Please let nobody ever have to use this method.
        if type(criticals) == str:
            raise ValueError("The addCriticals method should only be run on a list. To add a string, run the addCritical method")
        for critical in criticals:
            self.criticalList.append(critical)

    def toDict(self):
        dataDict = {
            "Passed" : self.passed,
            "Warning Count" : self.warningCount,
            "Error Count" : self.errorCount,
            "Inputs" : self.inputs,
            "Warnings" : self.warningList.copy(),
            "Errors" : self.errorList.copy(),
            "Critical Errors" : self.criticalList.copy()
        }
        return {self.testName : dataDict}

    def toJSON(self, indent:int=2):
        return json.dumps(self.toDict(), indent=indent)

    def dumpToLogger(self, logger:logging.Logger) -> None:
        logger.info("Dumping results for test %s" %self.testName)
        for inputType, files in self.inputs.items():
            for file in files:
                logger.info("Analyzed %s %s" %(inputType, file))
        logger.info("RESULT: %s" %(str(self)))
        for criticalError in self.criticalList:
            logger.critical(criticalError)
        for error in self.errorList:
            logger.error(error)
        for warning in self.warningList:
            logger.warning(warning)

    def __str__(self):
        if self.passed:
            passString = "PASSED"
        else:
            passString = "FAILED"
        outputString = "%s: %s | Errors: %s | Warnings: %s" %(self.testName, passString, self.errorCount, self.warningCount)
        if self.criticalList:
            outputString += " | CRITICAL ERRORS REPORTED!"
        return outputString
