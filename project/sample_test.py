# coding=utf-8

from typing                     import *
from lekit.File.Core            import tool_file
from lekit.Str.Core             import UnWrapper as UnWrapper2Str, word_segmentation
from lekit.Visual.WordCloud     import make_word_cloud
from docx.document              import Document as DocumentObject
from project.Core               import ProjectConfig
from lekit.LLM.LangChain.llama  import *

class DocxRuntime:
    def __init__(self, file:Union[str, tool_file]):
        self.file:  tool_file       = file if isinstance(file, tool_file) else tool_file(file_path=UnWrapper2Str(file))
        self.words: Dict[str, int]  = {}
        self.open()
    
    def open(self):
        if self.file.get_extension() == 'docx':
            self.file.close()
            self.docx:DocumentObject = self.file.load_as_docx()
        else:
            raise ValueError("Not a docx file")
    
    def append_words_config(self, sentence:str, **kwargs):
        result = word_segmentation(sentence, **kwargs)
        for item in result:
            current = UnWrapper2Str(item)
            if current not in self.words:
                self.words[current] = 1
            else:
                self.words[current] += 1
    def clear_words_config(self):
        self.words = {}
    def render_wordcloud(self, assets:tool_file) -> tool_file:
        if assets.is_dir() is False:
            assets = tool_file(UnWrapper2Str(assets)).back_to_parent_dir()
        
        words:List[Tuple[str, int]] = []
        for key, value in self.words.items():
            words.append((key, value))
        result = assets|"wordcould.html"
        make_word_cloud("wordcould", words).render(UnWrapper2Str(result))
        return result
    
    def buildup_result(self) -> List[str]:
        self.clear_words_config()
        result:List[str] = []
        current = self.docx
        for paragraph in current.paragraphs:
            current_text = paragraph.text
            result.append(current_text)
            self.append_words_config(current_text)
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
        target_n_ctx = 1024
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
            model_path=UnWrapper2Str(tool_file(current_config[SampleTest_LLm_Model_Path_FindKey])), n_ctx=target_n_ctx
            ),
            init_message=make_system_prompt(SampleTest_LLm_Model_SystemPrompt))
        
        # Build up auto runtime path
        assets_target_file = current_config.get_file("StreamingAssets/AutoRuntimePath.json", True)
        list_text = []
        for text in self.docx_runtime.buildup_result():
            list_text.append(llm_core(text).content)
            
        word_could_file = self.docx_runtime.render_wordcloud(current_config.get_file("StreamingAssets/", True))
            
        assets_target_file.open('w')
        assets_target_file.data={
            "Datas":        list_text,
            "WordCould":    UnWrapper2Str(word_could_file)
        }
        assets_target_file.save()
        