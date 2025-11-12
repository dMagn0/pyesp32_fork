from enum import Enum, auto

class OperationType(Enum):
    WRITE = "w"
    READ = "r"
    pass

class PinType(Enum):
    ANALOG = "a"
    DIGITAL = "d"
    pass



if __name__=="__main__":
    print(OperationType.READ.value)