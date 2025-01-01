from typing             import *
from lekit.File.Core    import *
from lekit.Str.Core     import *
from lekit.lazy         import GlobalConfig

ProjectDataDir = "Runtime/StreamingAssets/"
InternalResultOutputFileName = "AutoRuntimePath.json"

# In WebHandler.py, control main branch's key-field name of input file
InternalDesignDocumentationFieldName = "project"

class ProjectConfig(GlobalConfig):
    def __init__(self):
        super().__init__(ProjectDataDir, True)


