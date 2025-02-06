from typing             import *
from lekit.lazy         import GlobalConfig
from lekit.short        import *
from lekit.File.Core            import tool_file
from lekit.Str.Core             import UnWrapper as UnWrapper2Str, word_segmentation
from lekit.LLM.LangChain.llama  import *
from tqdm                       import tqdm
import logging
import os

#if os.path.exists("allow_logging.txt")==False:
#    logging.getLogger().setLevel(logging.ERROR)

ProjectDataDir = "Runtime/StreamingAssets/"
InternalResultOutputFileName = "AutoRuntimePath.json"

# In WebHandler.py, control main branch's key-field name of input file
InternalDesignDocumentationFieldName = "project"

class BasicTestCore(lvref[light_llama_core], ABC):
    config:     GlobalConfig = None
    @property
    def llm_core(self) -> light_llama_core:
        return self.ref_value
    @llm_core.setter
    def llm_core(self, value:light_llama_core):
        self.ref_value = value
    def __init__(self, llama:Optional[light_llama_core]=None):
        super().__init__(llama)
    @abstractmethod
    def build_model(self) -> bool:
        raise NotImplementedError("build_model is not implemented")
    def check_model(self, rebuild_key:str, current_config:GlobalConfig) -> bool:
        # Check config and get target property
        # Init current environment
        stats:          bool            = True
        if self.llm_core is None or (
            rebuild_key in current_config and current_config[rebuild_key] is True
            ):
            stats = self.build_model()
            current_config[rebuild_key] = False
            current_config.save_properties()
        return stats
    @abstractmethod
    def run(
        self,
        config:     GlobalConfig,
        input_file: tool_file,
        output_dir: tool_file
        ) -> Optional[Any]:
        raise NotImplementedError("run is not implemented")
    

