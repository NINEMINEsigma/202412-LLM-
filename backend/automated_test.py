# coding=utf-8
from backend.Internal   import *
from backend.sample_test import SampleTest_KeysTemplate

AutomatedTest_LLm_Model_Path_FindKey    = r"AutomatedTest_LLM_Model"
AutomatedTest_LLM_Model_Max_Ctx_Len     = r"AutomatedTest_LLM_n_ctx"
AutomatedTest_LLM_Model_Max_KWargs      = r"AutomatedTest_LLM_Model_Max_KWargs"
AutomatedTest_LLM_Model_SystemPrompt    = '''
你现在是一名软件测试员，正在完成一项软件测试任务。
你接下来将收到一些测试用例并需要参考这些用例，
解读给定网页的html代码并通过提供的selenium封装函数进行自动化测试。

你需要完成以下任务：
1. 解读给定网页的html代码
2. 对当前网页进行自动化测试, 有错误则进行记录, 没有错误则返回空的记录列表
3. 打开当前网页可以通向的其他页面

你需要完成以下步骤：
1. 解读给定网页的html代码
2. 通过提供的selenium封装函数进行自动化测试
3. 将测试结果记录到测试报告中
4. 打开当前网页可以通向的其他页面

你需要完成以下要求：
1. 测试用例如果无法解读或者无效, 则自行跳过并进行当前网页的测试
2. 输出的测试报告需要包含执行的测试用例, 测试结果, 测试错误等信息
3. 测试报告的末尾需要汇总当前网页通向的其他页面的链接

测试用例列表的格式如下:
{
    "Datas":[
'''+str(SampleTest_KeysTemplate)+'''
    ]
}
测试报告的格式如下:


你输出的文字需要与获取的文档主要使用的语言相同
'''
AutomatedTest_LLM_Model_Check_Rebulid   = r"AutomatedTest_LLM_Rebulid"
AutomatedTest_Target_URL                = r"AutomatedTest_Target_URL"

class AutomatedTestCore(BasicTestCore):
    functioncall:   light_llama_functioncall                            = None

    def __init__(self, url:str, llama:Optional[light_llama_core]=None):
        super().__init__(llama)

    @override
    def build_model(self) -> bool:
        # Check config and get target property
        self.config.LogMessage("Sample Test Model Currently Rebuild")
        stats = True
        # AutomatedTest_LLm_Model_Path_FindKey init
        Model_Path = self.config.FindItem(AutomatedTest_LLm_Model_Path_FindKey)
        if Model_Path is None:
            stats = False
        target_n_ctx = self.config.FindItem(AutomatedTest_LLM_Model_Max_Ctx_Len, 1024)
        model_kwargs:dict = self.config.FindItem(AutomatedTest_LLM_Model_Max_KWargs, {})
        model_kwargs.update({
            "model_path" :  Model_Path,
            "n_ctx" :       target_n_ctx,
        })
        
        if stats is False:
            self.config.save_properties()
            self.config.LogMessageOfPleaseCompleteConfiguration()
            return False

        # Build llm core
        self.llm_core:light_llama_core       = light_llama_core(
            model                       = ChatLlamaCpp(**model_kwargs),
            init_message                = make_system_prompt(AutomatedTest_LLM_Model_SystemPrompt),
            is_record_result_to_history = False,
            )
        raise NotImplementedError("TODO")
        #self.functioncall = make_llama_functioncall(
        #    self.llm_core,
        #    sample_create,
        #    "sample_create_function",
        #    )
        return True

    def run_with_list_of_str(
        self,
        AutoRuntimePath:    Optional[tool_file],
        output_dir:         tool_file
        ):
        # Check config and get target property
        # Init current environment
        if self.check_model(AutomatedTest_LLM_Model_Check_Rebulid, self.config) is False:
            return None

        self.llm_core.clear_hestroy()

        # Build up auto runtime path
        assets_target_file = output_dir|InternalResultOutputFileName
        result_container = []
        for index in tqdm(range(len(input_list_text))):
            text = input_list_text[index]
            if len(text) < self.__ignore_when_text_length_is_too_short:
                continue
            try:
                result_container.extend(self.functioncall(text)["sample_create_function"])
            except BaseException as ex:
                self.config.LogError(f"{ex}")
                self.config.LogError(f"{traceback.format_exc()}")
                self.config.LogError(f"current text is <{text}>")

        assets_target_file.data={
            "Datas":        result_container,
        }
        return assets_target_file

    @override
    def run(
        self,
        config:             GlobalConfig,
        AutoRuntimePath:    Optional[tool_file],
        output_dir:         tool_file
        ):
        # run core
        self.config=config
        with self.run_with_list_of_str(AutoRuntimePath, output_dir) as assets_target_file:
            if assets_target_file is None:
                return None
            # Save result
            assets_target_file.save()
            return assets_target_file
        raise NotImplementedError("Should not reach here")

    
    
    
    