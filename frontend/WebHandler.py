from lekit.Lang             import *
from lekit.Web.Core         import light_handler
from lekit.File.Core        import tool_file

from backend.Internal       import *
from backend.sample_test    import SampleTestCore

WebHandlerWorkerCounter:    Dict[str, left_value_reference[int]]    = {}

CurrentSampleTestCore:      SampleTestCore                          = {}

def run_main_core_with_design_documentation(
    source_file:tool_file,
    result_file:tool_file
    ):
    config = ProjectConfig()
    result_file.try_create_parent_path()

class project_backend_handler(light_handler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server, callback=self.callback)

    def callback(self, handler:light_handler, type:str):
        return self.virsual_callback(handler, type)

    def main_branch(self) -> bytes:
        config = ProjectConfig()
        # 解析 multipart/form-data
        boundary = self.headers['Content-Type'].split('boundary=')[-1]
        parts = self.temp_result.split(b'--' + boundary.encode())

        for part in parts:
            if b'Content-Disposition' in part and f'name="{InternalDesignDocumentationFieldName}"'.encode("utf-8") in part:
                # 提取文件名
                filename = part.split(b'filename="')[-1].split(b'"')[0]
                file_content = part.split(b'\r\n\r\n')[-1].rstrip(b'--')

                # 保存文件
                current_time = 0
                current_origin_filename = filename.decode()
                if current_origin_filename in WebHandlerWorkerCounter:
                    current_time = WebHandlerWorkerCounter[current_origin_filename].ref_value
                    WebHandlerWorkerCounter[current_origin_filename].ref_value += 1
                else:
                    WebHandlerWorkerCounter[current_origin_filename] = left_value_reference(1)
                current_target_filename = f"{current_time}_{current_origin_filename}"
                temp_file = config.get_file(f"main/sources/{current_target_filename}", True)
                temp_file.open('wb')
                temp_file.data = file_content
                temp_file.save_as_binary()

                # 核心处理
                current_response_file = config.get_file(
                    f"main/results/{tool_file(current_target_filename).get_filename(True)}/{InternalResultOutputFileName}"
                    )
                run_main_core_with_design_documentation(temp_file, current_response_file)
                current_response_file.open("rb")
                response = current_response_file.load_as_binary()

                # 释放资源
                temp_file.close()
                temp_file.remove()
                current_response_file.close()
                current_response_file.back_to_parent_dir().remove()
                WebHandlerWorkerCounter[current_origin_filename].ref_value -= 1

                return response
        return None

    def virsual_callback(self, handler:light_handler, type:str):
        config = ProjectConfig()
        if type == 'get':
            config.LogWarning("get operator current is empty")
        elif type == 'post':
            if self.path == '/main':
                return self.main_branch()
            return None
        elif type == 'put':
            config.LogWarning("put operator current is empty")
        elif type == 'delete':
            config.LogWarning("delete operator current is empty")
        else:
            config.LogWarning("unknown operator current is empty")
        return handler.temp_result
