# coding=utf-8
from lekit.Visual.WordCloud     import make_word_cloud
from docx.document              import Document as DocumentObject
from backend.Internal           import *

meaningless_words = [
    "的","地","得","是","否","对","错",
    ",",".","!","?","，","。","！","？","：","；","“","”","‘","’","《","》","（","）","【","】",
]

SampleTest_LLM_Paragraph_Length     = r"SampleTest_LLM_Paragraph_Length"

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
            if key not in meaningless_words:
                words.append((key, value))
        result = assets|"wordcould.html"
        make_word_cloud("wordcould", words).render(UnWrapper2Str(result))
        return result

    def buildup_result(self) -> List[str]:
        current_config:ProjectConfig = ProjectConfig()
        self.clear_words_config()
        result:List[str] = []
        current = self.docx
        
        buffer:str          = ""
        buffer_length:int   = 1024
        if SampleTest_LLM_Paragraph_Length in current_config:
            buffer_length = current_config[SampleTest_LLM_Paragraph_Length]
        else:
            current_config.LogWarning(f"{SampleTest_LLM_Paragraph_Length} is not found, current using default[{buffer_length}]")
        for paragraph in current.paragraphs:
            current_text = paragraph.text
            if len(buffer)+len(current_text)<buffer_length:
                buffer += "\n"+current_text
            else:
                self.append_words_config(buffer)
                result.append(buffer)
                buffer = current_text
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
SampleTest_LLM_Ignore_2Short        = r"SampleTest_Ignore_Length"
SampleTest_LLM_Model_SystemPrompt   = '''
你现在是一名软件测试员，正在完成一项软件测试任务。
你接下来将收到该软件的设计文档，并获取生成基于此内容的测试用例。
你需要以特定格式输出测试用例列表。
格式如下。

{
    "Datas":[
'''+str(SampleTest_KeysTemplate)+'''
    ]
}

这样就生成了一个样例，你需要按需生成一个或多个用例, 在你认为不需要生成时则返回空列表。
你输出的文字需要与获取的文档主要使用的语言相同, 如果你不能完成判断则使用utf8编码的中文输出
'''
SampleTest_LLM_Model_Check_Rebulid = r"SampleTest_LLM_Rebulid"

class SingleSample(BaseModel):
    '''
    这是一个单独的样例
    '''
    current_scene:      str = Field(description="当前所处的场景The current scene of this sample")
    current_module:     str = Field(description="当前所处的模块The current module of this sample")
    current_operation:  str = Field(description="即将进行的操作The current operation of this sample")
    current_expect:     str = Field(description="操作后预期结果The current expect of this sample")
class SampleList(BaseModel):
    '''
    这是一个样例列表, 如果不需要生成用例则为空, 否则将包含多个测试用例
    '''
    datas:  List[SingleSample] = Field(description="测试用例列表The list of sample")

@FunctionTool("sample_create_function", args_schema=SampleList)
def sample_create(
    datas:  List[SingleSample]
    ):
    """create samples."""
    return [{
        "Scene":      item.current_scene,
        "Module":     item.current_module,
        "Operation":  item.current_operation,
        "Expect":     item.current_expect
    } for item in datas]

class SampleTestCore(BasicTestCore):
    web_codes:     Dict[WebCodeType, Dict[URL_or_Marking_Type, str]]   = {}
    functioncall:  light_llama_functioncall                            = None
    __ignore_when_text_length_is_too_short: int                        = None
    
    error_map:     Dict[str, Any]                                      = {}
    
    def __init__(self, llama:Optional[light_llama_core]=None):
        super().__init__(llama)

    @override
    def build_model(self) -> bool:
        # Check config and get target property
        current_config:ProjectConfig = ProjectConfig()
        current_config.LogMessage("Sample Test Model Currently Rebuild")
        stats = True
        target_n_ctx = 1024
        target_ignore_when_text_length_is_too_short = 5
        if SampleTest_LLM_Model_Path_FindKey not in current_config or current_config[SampleTest_LLM_Model_Path_FindKey] == "set you model":
            current_config.LogPropertyNotFound(SampleTest_LLM_Model_Path_FindKey)
            current_config[SampleTest_LLM_Model_Path_FindKey] = "set you model"
            stats = False
        if SampleTest_LLM_Model_Max_Ctx_Len not in current_config:
            current_config.LogWarning(f"{SampleTest_LLM_Model_Max_Ctx_Len} is not found, current using default[{target_n_ctx}]")
        else:
            target_n_ctx = current_config[SampleTest_LLM_Model_Max_Ctx_Len]
        if SampleTest_LLM_Ignore_2Short not in current_config:
            current_config.LogWarning(f"{SampleTest_LLM_Ignore_2Short} is not found, current using default[{target_ignore_when_text_length_is_too_short}]")
        else:
            target_ignore_when_text_length_is_too_short = current_config[SampleTest_LLM_Ignore_2Short]

        if stats is False:
            current_config.save_properties()
            current_config.LogMessageOfPleaseCompleteConfiguration()
            return False

        # Build llm core
        self.llm_core:light_llama_core       = light_llama_core(
            ChatLlamaCpp(
                model_path              = UnWrapper2Str(tool_file(current_config[SampleTest_LLM_Model_Path_FindKey])),
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
        self.__ignore_when_text_length_is_too_short = target_ignore_when_text_length_is_too_short
        return True

    def run_with_list_of_str(
        self,
        input_list_text:    Sequence[str],
        output_dir:         tool_file
        ):
        # Check config and get target property
        # Init current environment
        current_config: ProjectConfig   = ProjectConfig()
        if self.check_model(SampleTest_LLM_Model_Check_Rebulid, current_config) is False:
            return None

        self.llm_core.clear_hestroy()

        # Build up auto runtime path
        assets_target_file = output_dir|InternalResultOutputFileName
        result_container = []
        for index in tqdm(range(len(input_list_text))):
            text = input_list_text[index]
            if len(text) < self.__ignore_when_text_length_is_too_short:
                print_colorful(ConsoleFrontColor.YELLOW,text, is_reset=True)
                continue
            else:
                print_colorful(ConsoleFrontColor.GREEN,text,is_reset=True)
            try:
                result_container.extend(self.functioncall(text)["sample_create_function"])
            except BaseException as ex:
                self.error_map[text]=ex
                current_config.LogError(f"Error when running \"{text[:20]}...\" : {ex}")
            os.system('cls') or os.system('clear')

        assets_target_file.data={
            "Datas":        result_container,
        }
        return assets_target_file

    @override
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
        with self.run_with_list_of_str(list_text, output_dir) as assets_target_file:
            if assets_target_file is None:
                return None
            assets_target_file.data["word_cloud"] = UnWrapper2Str(word_cloud_file)
            # Save result
            assets_target_file.save()
            return assets_target_file
        raise NotImplementedError("Should not reach here")












