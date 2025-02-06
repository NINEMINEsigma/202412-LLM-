# coding=utf-8
from lekit.Visual.WordCloud     import make_word_cloud
from docx.document              import Document as DocumentObject
from backend.Internal           import *
import                                 math

meaningless_words = [
    "的","地","得","是","否","对","错",
    ",",".","!","?","，","。","！","？","：","；","“","”","‘","’","《","》","（","）","【","】", " ",
    "会","这种","到",
]

SampleTest_LLM_Paragraph_Length         = r"SampleTest_LLM_Paragraph_Length"
SampleTest_DocxRuntime_StopWord_File    = r"SampleTest_DocxRuntime_StopWord_File"

def remove_keys_below_threshold(input:List[Tuple[str, int]]):
    # 获取列表中元组第二个元素的最大值
    max_value = max(item[1] for item in input)
    # 计算阈值
    threshold = math.log(max_value * 0.25, 1.2)
    # 创建一个新的列表，只包含大于等于阈值的元组
    filtered_list = [item for item in input if item[1] >= threshold]
    
    return filtered_list
class DocxRuntime: 
    '''用来读取并存储docx文件中的词频'''
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
    def render_wordcloud(self, config:GlobalConfig, assets:tool_file) -> tool_file:
        if assets.is_dir() is False:
            assets = tool_file(UnWrapper2Str(assets)).back_to_parent_dir()
            
        # 加载停用词表
        stop_words = set()
        if (SampleTest_DocxRuntime_StopWord_File in config and 
            tool_file(config[SampleTest_DocxRuntime_StopWord_File]).exists()):
            with open(config[SampleTest_DocxRuntime_StopWord_File], "r", encoding="utf-8") as f:
                for line in f:
                    stop_words.add(line.strip())

        # 去除停用词和低频词
        words:List[Tuple[str, int]] = []
        for key, value in self.words.items():
            if key not in meaningless_words and key not in stop_words:
                words.append((key, value))
        result = assets|"wordcould.html"
        make_word_cloud("wordcould", remove_keys_below_threshold(words)).render(UnWrapper2Str(result))
        return result

    def build_text_list(self, config:GlobalConfig) -> List[str]:
        self.clear_words_config()
        result:List[str] = []
        current = self.docx
        
        # Buffer init
        buffer:str          = ""
        buffer_length:int   = config.FindItem(SampleTest_LLM_Paragraph_Length, 1024)
        # Link Garagraph to build result
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
SampleTest_LLM_Model_KWargs         = r"SampleTest_LLM_Model_KWargs"
SampleTest_LLM_FunctionCall_Try     = r"SampleTest_LLM_FunctionCall_Try"
SampleTest_LLM_Model_SystemPrompt   = '''
你现在是一名软件测试员，正在完成一项软件测试任务。
你接下来将收到该软件的设计文档，并获取生成基于此内容的测试用例。

你需要完成以下任务：
1. 解读给定的文档并生成对应内容的测试用例

你需要完成以下步骤：
1. 接收给定的文档(可能是部分)
2. 解读文档内容
3. 识别当前是什么应用场景(Scene)
4. 识别当前是什么模块(Module)
5. 识别当前需要进行的操作(Operation)
6. 识别当前操作后预期结果(Expect)
7. 生成基于文档内容的测试用例
8. 如果仍有用例需要生成, 重复以上步骤
9. 返回生成的测试用例列表

你需要完成以下要求：
1. 如果当前给定的文档(可能是部分)不包含需要测试的内容, 则返回空的测试用例列表
2. 如果当前给定的文档(可能是部分)包含需要测试的内容, 则生成对应的测试用例, 可能是多个

你需要以特定格式输出测试用例列表, 格式如下:
{
    "Datas":[
'''+str(SampleTest_KeysTemplate)+'''
    ]
}

这样就生成了一个样例，你需要按需生成一个或多个用例, 在你认为不需要生成时则返回空列表。

假如收到的文本如下:
    登录时输入用户名与密码, 若用户名与密码正确则出现登录成功弹窗并跳转到主页, 若用户名或密码错误则出现登录失败弹窗
那你应该生成的用例则应该如下列表:
1. 场景:登录 模块:登录 操作:输入正确用户名与正确密码 预期:登录成功弹窗
2. 场景:登录 模块:登录 操作:输入正确用户名与错误密码 预期:登录失败弹窗
3. 场景:登录 模块:登录 操作:输入错误用户名与正确密码 预期:登录失败弹窗
4. 场景:登录 模块:登录 操作:输入错误用户名与错误密码 预期:登录失败弹窗

你输出的文字需要与获取的文档主要使用的语言相同
'''
SampleTest_LLM_Model_Check_Rebulid = r"SampleTest_LLM_Rebulid"

class SingleSample(BaseModel):
    '''
    这是一个单独的样例
    '''
    Scene:      str = Field(description="当前所处的场景The current scene of this sample")
    Module:     str = Field(description="当前所处的模块The current module of this sample")
    Operation:  str = Field(description="即将进行的操作The current operation of this sample")
    Expect:     str = Field(description="操作后预期结果The current expect of this sample")
class SampleList(BaseModel):
    '''
    这是一个样例列表, 如果不需要生成用例则为空, 否则将包含多个测试用例
    '''
    datas:  List[SingleSample] = Field(description="测试用例列表The list of sample")

@FunctionTool("sample_create_function", args_schema=SampleList)
def sample_create(
    datas:  List[SingleSample]
    ) -> List[Dict[str, str]]:
    """create samples."""
    return [
        {
            "Scene":      item.Scene,
            "Module":     item.Module,
            "Operation":  item.Operation,
            "Expect":     item.Expect
        } for item in datas
    ]

class SampleTestCore(BasicTestCore):
    web_codes:      Dict[WebCodeType, Dict[URL_or_Marking_Type, str]]   = {}
    functioncall:   light_llama_functioncall                            = None
    __ignore_when_text_length_is_too_short: int                         = None
    
    error_map:      Dict[str, Any]                                      = {}
    
    def __init__(self, llama:Optional[light_llama_core]=None):
        super().__init__(llama)

    @override
    def build_model(self) -> bool:
        # Check config and get target property
        self.config.LogMessage("Sample Test Model Currently Rebuild")
        stats = True
        # Check Model Path
        Model_Path = self.config.FindItem(SampleTest_LLM_Model_Path_FindKey)
        if Model_Path is None:
            stats = False
        # Context Length
        target_n_ctx = self.config.FindItem(SampleTest_LLM_Model_Max_Ctx_Len, 1024)
        # Limit Text Length
        target_ignore_when_text_length_is_too_short = self.config.FindItem(SampleTest_LLM_Ignore_2Short)
        if target_ignore_when_text_length_is_too_short is None:
            target_ignore_when_text_length_is_too_short = 12
            self.config.LogWarning(f"{SampleTest_LLM_Ignore_2Short} is not found, current using default[{target_ignore_when_text_length_is_too_short}]")
        # SampleTest_LLM_Model_KWargs
        target_kwargs:dict = self.config.FindItem(SampleTest_LLM_Model_KWargs,{})
        target_kwargs.update({
            "model_path":   Model_Path,
            "n_ctx":        target_n_ctx,
        })
        
        if stats is False:
            self.config.save_properties()
            self.config.LogMessageOfPleaseCompleteConfiguration()
            return False

        # Build llm core
        self.llm_core:light_llama_core       = light_llama_core(
            model                       = ChatLlamaCpp(**target_kwargs),
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
        if self.check_model(SampleTest_LLM_Model_Check_Rebulid, self.config) is False:
            return None

        self.llm_core.clear_hestroy()
        max_functioncall_try:int = self.config.FindItem(SampleTest_LLM_FunctionCall_Try, 5)

        # Build up auto runtime path
        assets_target_file = output_dir|InternalResultOutputFileName
        result_container = []
        tqdmiter = tqdm(
            range(len(input_list_text)),
            unit="Block",
            )
        for index in tqdmiter:
            text = input_list_text[index]
            show_text = limit_str(text, 128)
            if len(text) < self.__ignore_when_text_length_is_too_short:
                self.config.LogMessage(show_text,ConsoleFrontColor.YELLOW)
                continue
            else:
                self.config.LogMessage(show_text,ConsoleFrontColor.GREEN)
            result:Dict[str, Any] = {}
            try:
                result = self.functioncall(text)
                recall_times = int(max_functioncall_try)
                while "sample_create_function" not in result and recall_times>0:
                    self.config.LogWarning("Waiting for the function to complete")
                    result = self.functioncall(text)
                    recall_times-=1
                current:List[Dict[str, str]] = result["sample_create_function"]
                self.config.LogMessage(current,ConsoleFrontColor.BLUE)
                result_container.extend(current)
            except KeyboardInterrupt as ex:
                assets_target_file.data={
                    "Datas":        result_container,
                    "Error":        self.error_map,
                }
                assets_target_file.save()
                exit(0)
            except BaseException as ex:
                self.error_map[text]=ex
                self.config.LogError(f"Error<{ex.__class__.__name__}:{ex}>/Result<{result}> when running \"{show_text}\"")
            finally:
                assets_target_file.data={
                    "Datas":        result_container,
                    "Error":        self.error_map,
                }
                
        # Save result to file
        assets_target_file.data={
            "Datas":        result_container,
            "Error":        self.error_map,
        }
        return assets_target_file

    @override
    def run(
        self,
        config:     GlobalConfig,
        input_file: tool_file,
        output_dir: tool_file
        ):
        # Check config and get target property
        # Init current environment and build docx
        self.config                     = config
        self.error_map.clear()
        docx_runtime:   DocxRuntime     = DocxRuntime(input_file)
        list_text:      List[str]       = docx_runtime.build_text_list(config)
        word_cloud_file:tool_file       = docx_runtime.render_wordcloud(config, output_dir)

        # run core
        assets_target_file = self.run_with_list_of_str(list_text, output_dir)
        if assets_target_file is None:
            return None
        # Combine Data
        assets_target_file.data["word_cloud"] = UnWrapper2Str(word_cloud_file)
        assets_target_file.data["input_file"] = UnWrapper2Str(input_file)
        # Save result
        assets_target_file.save()
        return assets_target_file












