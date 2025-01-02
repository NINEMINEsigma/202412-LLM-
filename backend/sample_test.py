# coding=utf-8

from typing                     import *
from lekit.File.Core            import tool_file
from lekit.Str.Core             import UnWrapper as UnWrapper2Str, word_segmentation
from lekit.Visual.WordCloud     import make_word_cloud
from docx.document              import Document as DocumentObject
from backend.Internal           import *
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
    "Scene":"当前场景",
    "Module":"当前模块",
    "Operation":"当前操作",
    "Expect":"当前预期"
}

SampleTest_LLM_Model_Path_FindKey   = r"SampleTest_LLM_Model"
SampleTest_LLM_Model_Max_Ctx_Len    = r"SampleTest_LLM_n_ctx"
SampleTest_LLM_Model_SystemPrompt   = '''
你现在是一名软件测试工作员，正在完成一项软件测试任务。
你接下来将收到该软件的设计文档(可能是的一部分)，并获取生成基于此内容的测试用例。
你需要以特定格式输出测试用例列表。
格式如下。

{
    "Datas":[
'''+str(SampleTest_KeysTemplate)+'''
    ]
}

你的输出需要与获取的文档主要使用的语言相同, 如果你不能完成判断则使用utf8编码的中文输出
'''
SampleTest_LLM_Model_Check_Rebulid = r"SampleTest_LLM_Rebulid"

class SingleSample(BaseModel):
    current_scene:      str = Field(description="The current scene of this sample")
    current_module:     str = Field(description="The current module of this sample")
    current_operation:  str = Field(description="The current operation of this sample")
    current_expect:     str = Field(description="The current expect of this sample")
    has_sample_to_create:bool = Field(description="Current input has sample must to create?")

@FunctionTool("sample_create_function", args_schema=SingleSample)
def sample_create(
    current_scene:      str,
    current_module:     str,
    current_operation:  str,
    current_expect:     str,
    has_sample_to_create:bool
    ):
    """create one sample."""
    if has_sample_to_create is False:
        return None
    return {
        "Scene":      current_scene,
        "Module":     current_module,
        "Operation":  current_operation,
        "Expect":     current_expect
    }

class SampleTestCore:
    def __init__(self):
        self.web_codes:     Dict[WebCodeType, Dict[URL_or_Marking_Type, str]]   = {}
        self.llm_core:      light_llama_core                                    = None
        self.functioncall:  light_llama_functioncall                            = None

    def build_model(self) -> bool:
        # Check config and get target property
        current_config:ProjectConfig = ProjectConfig()
        current_config.LogMessage("Sample Test Model Currently Rebuild")
        stats = True
        target_n_ctx = 1024
        if SampleTest_LLM_Model_Path_FindKey not in current_config or current_config[SampleTest_LLM_Model_Path_FindKey] == "set you model":
            current_config.LogPropertyNotFound(SampleTest_LLM_Model_Path_FindKey)
            current_config[SampleTest_LLM_Model_Path_FindKey] = "set you model"
            stats = False
        if SampleTest_LLM_Model_Max_Ctx_Len not in current_config:
            current_config.LogWarning(f"{SampleTest_LLM_Model_Max_Ctx_Len} is not found, current using default[{target_n_ctx}]")

        if stats is False:
            current_config.save_properties()
            current_config.LogMessageOfPleaseCompleteConfiguration()
            return False

        # Build llm core
        self.llm_core:light_llama_core       = light_llama_core(
            ChatLlamaCpp(
                model_path=UnWrapper2Str(tool_file(current_config[SampleTest_LLM_Model_Path_FindKey])),
                n_ctx=target_n_ctx,

                ),
            init_message                = make_system_prompt(SampleTest_LLM_Model_SystemPrompt),
            is_record_result_to_history = False,
            )
        self.functioncall = make_llama_functioncall(
            self.llm_core,
            sample_create,
            "sample_create_function",
            )
        return True

    def run_with_list_of_str(
        self,
        input_list_text:    Sequence[str],
        output_dir:         tool_file
        ):
        # Check config and get target property
        # Init current environment
        current_config: ProjectConfig   = ProjectConfig()
        stats:          bool            = True

        if self.llm_core is None or (
            SampleTest_LLM_Model_Check_Rebulid in current_config and current_config[SampleTest_LLM_Model_Check_Rebulid] is True
            ):
            stats = self.build_model()
            current_config[SampleTest_LLM_Model_Check_Rebulid] = False
            current_config.save_properties()

        if stats is False:
            return None

        self.llm_core.clear_hestroy()

        # Build up auto runtime path
        assets_target_file = output_dir|InternalResultOutputFileName
        result_container = []
        for text in input_list_text:
            result_container.append(self.functioncall(text)["sample_create_function"])

        assets_target_file.data={
            "Datas":        result_container,
        }
        return assets_target_file


    def run(
        self,
        input_file: tool_file,
        output_dir: tool_file
        ):
        # Check config and get target property
        # Init current environment and build docx
        docx_runtime:  DocxRuntime                                         = DocxRuntime(input_file)
        list_text = docx_runtime.buildup_result()
        word_cloud_file = docx_runtime.render_wordcloud(output_dir)

        # run core
        assets_target_file = self.run_with_list_of_str(list_text, output_dir)
        assets_target_file.data["word_cloud"] = UnWrapper2Str(word_cloud_file)

        # Save result
        assets_target_file.open('w')
        assets_target_file.save()
        assets_target_file.close()
        return assets_target_file












