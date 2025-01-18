from typing             import *
from lekit.lazy         import GlobalConfig
from lekit.short        import *
from lekit.File.Core            import tool_file
from lekit.Str.Core             import UnWrapper as UnWrapper2Str, word_segmentation
from lekit.LLM.LangChain.llama  import *
from tqdm                       import tqdm

ProjectDataDir = "Runtime/StreamingAssets/"
InternalResultOutputFileName = "AutoRuntimePath.json"

# In WebHandler.py, control main branch's key-field name of input file
InternalDesignDocumentationFieldName = "project"

class ProjectConfig(GlobalConfig):
    def __init__(self):
        super().__init__(ProjectDataDir, True)


