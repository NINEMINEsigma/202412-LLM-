# coding=utf-8
from backend.Internal   import *

AutomatedTest_LLm_Model_Path_FindKey   = r"AutomatedTest_LLM_Model"
AutomatedTest_LLM_Model_Max_Ctx_Len    = r"AutomatedTest_LLM_n_ctx"
AutomatedTest_LLM_Model_SystemPrompt        = r'''
You are a web search assistant that helps people find information. 
User will you give you a question.
 Your task is to answer as faithfully as you can. 
 While answering think step-bystep and justify your answer.

You have access to the following tools:
...

'''
AutomatedTest_LLM_Model_Check_Rebulid = r"AutomatedTest_LLM_Rebulid"

class AutomatedTestCore(lvref[light_llama_core]):
    @property
    def llm_core(self) -> light_llama_core:
        return self.ref_value
    @llm_core.setter
    def llm_core(self, value:light_llama_core):
        self.ref_value = value
        return value
    functioncall:   light_llama_functioncall                            = None
    target_url:     str                                                 = "www.bing.com"

    def __init__(self, url:str, llama:Optional[light_llama_core]=None):
        super().__init__(llama)
        self.target_url = url

    def build_model(self) -> bool:
        # Check config and get target property
        current_config:ProjectConfig = ProjectConfig()
        current_config.LogMessage("Sample Test Model Currently Rebuild")
        stats = True
        target_n_ctx = 1024
        # AutomatedTest_LLm_Model_Path_FindKey init
        model_path = current_config.FindItem(AutomatedTest_LLm_Model_Path_FindKey)
        if model_path is None or model_path == "set you model":
            current_config[AutomatedTest_LLm_Model_Path_FindKey] = "set you model"
            stats = False
        # AutomatedTest_LLM_Model_Max_Ctx_Len init
        if AutomatedTest_LLM_Model_Max_Ctx_Len not in current_config:
            current_config.LogWarning(f"{AutomatedTest_LLM_Model_Max_Ctx_Len} is not found, current using default[{target_n_ctx}]")
        else:
            target_n_ctx = current_config.FindItem(AutomatedTest_LLM_Model_Max_Ctx_Len)

        if stats is False:
            current_config.save_properties()
            current_config.LogMessageOfPleaseCompleteConfiguration()
            return False

        # Build llm core
        self.llm_core:light_llama_core       = light_llama_core(
            ChatLlamaCpp(
                model_path=UnWrapper2Str(tool_file(model_path)),
                n_ctx=target_n_ctx,

                ),
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
        input_list_text:    Sequence[str],
        output_dir:         tool_file
        ):
        # Check config and get target property
        # Init current environment
        current_config: ProjectConfig   = ProjectConfig()
        stats:          bool            = True

        if self.llm_core is None or (
            AutomatedTest_LLM_Model_Check_Rebulid in current_config and current_config[AutomatedTest_LLM_Model_Check_Rebulid] is True
            ):
            stats = self.build_model()
            current_config[AutomatedTest_LLM_Model_Check_Rebulid] = False
            current_config.save_properties()

        if stats is False:
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
                current_config.LogError(f"{ex}")
                current_config.LogError(f"{traceback.format_exc()}")
                current_config.LogError(f"current text is <{text}>")

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

    
    
    
    