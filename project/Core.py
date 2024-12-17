from typing             import *
from lekit.File.Core    import *
from lekit.Str.Core     import *
from lekit.lazy         import GlobalConfig

ProjectDataDir = "Runtime/Data"

class ProjectConfig(GlobalConfig):
    def __init__(self):
        super().__init__(ProjectDataDir, True)
        
    
        