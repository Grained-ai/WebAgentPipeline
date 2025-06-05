# exceptions.py

class QCException(Exception):
    """Base exception for all QC-related errors"""
    pass


# Flow related
class FlowException(QCException):
    """Base class for flow-level exceptions"""
    pass


class FlowModification(FlowException):
    pass


class FlowCheck(FlowException):
    pass


class FlowLoading(FlowException):
    pass


# Step related
class StepException(QCException):
    """Base class for step-level exceptions"""
    pass


class StepModification(StepException):
    pass


class StepCheck(StepException):
    pass


class StepLoading(StepException):
    pass


# Setup related
class SetupException(QCException):
    pass
