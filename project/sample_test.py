# coding=utf-8

from typing                     import *
from lekit.File.Core            import tool_file
from lekit.Str.Core             import UnWrapper
from docx.document              import Document as DocumentObject
from project.Core               import ProjectConfig
from lekit.LLM.LangChain.llama  import *

class DocxRuntime:
    def __init__(self, file:Union[str, tool_file]):
        self.file = file if isinstance(file, tool_file) else tool_file(file_path=UnWrapper(file))
        self.open()
        
    def open(self):
        if self.file.get_extension() == 'docx':
            self.file.close()
            self.docx:DocumentObject = self.file.load_as_docx()
        else:
            raise ValueError("Not a docx file")
        
    def read_all(self) -> List[str]:
        result:List[str] = []
        current = self.docx
        for paragraph in current.paragraphs:
            result.append(paragraph.text)
        self.data = result
        return result

WebCodeType = Literal['html', 'js', 'css', 'json', 'xml', 'yaml', 'yml', 'markdown', 'md', 'txt']
URL_or_Marking_Type = str

SampleTest_KeysTemplate = {
    "Scene":"current scene",
    "Module":"current module",
    "Operation":"current operation",
    "Expect":"expected result"
}

SampleTest_LLm_Model_Path_FindKey   = r"SampleTest_LLM_Model"
SampleTest_LLM_Model_Max_Ctx_Len    = r"SampleTest_LLM_n_ctx"
SampleTest_LLm_Model_SystemPrompt   = '''
You are a software testing engineer who is completing a software testing task.
You will then receive a design document for the software, and you will need to get all the test cases you should have based on this document.
You need to output a list of test cases in a specific format.
This list is made up of json, which has four key-value pairs, which are current scene, current module, current operation, and expected result.
The format is as follows.

{
    "Datas":[
'''+str(SampleTest_KeysTemplate)+'''
    ]
}

In particular, please translate the output into Chinese
'''

class SampleTestCore:
    def __init__(self, file:Union[str, tool_file]):
        self.docx_runtime:  DocxRuntime                                         = DocxRuntime(file)
        self.web_codes:     Dict[WebCodeType, Dict[URL_or_Marking_Type,str]]    = {}
        
    def run(self):
        # Check config and get target property
        current_config:ProjectConfig = ProjectConfig()
        stats = True
        target_n_ctx = 512
        if SampleTest_LLm_Model_Path_FindKey not in current_config or current_config[SampleTest_LLm_Model_Path_FindKey] == "set you model":
            current_config.LogPropertyNotFound(SampleTest_LLm_Model_Path_FindKey)
            current_config[SampleTest_LLm_Model_Path_FindKey] = "set you model"
            stats = False
        if SampleTest_LLM_Model_Max_Ctx_Len not in current_config:
            current_config.LogWarning(f"{SampleTest_LLM_Model_Max_Ctx_Len} is not found, current using default[{target_n_ctx}]")
            
        if stats is False:
            current_config.save_properties()
            return
            
        # Build llm core
        llm_core:light_llama_core       = light_llama_core(ChatLlamaCpp(
            model_path=UnWrapper(tool_file(current_config[SampleTest_LLm_Model_Path_FindKey])), n_ctx=target_n_ctx
            ),
            init_message=make_system_prompt(SampleTest_LLm_Model_SystemPrompt))
        
        # Build up auto runtime path
        assets_target_file = current_config.get_file("StreamingAssets/AutoRuntimePath.json", True)
        list_text = []
        for text in self.docx_runtime.read_all():
            list_text.append(llm_core(text).content)
        assets_target_file.open('w')
        assets_target_file.data={
            "Datas":list_text
        }
        assets_target_file.save()
        