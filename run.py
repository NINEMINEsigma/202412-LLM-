# coding=utf-8

from lekit.lazy import *
from backend.Internal import *
from backend.sample_test import SampleTestCore

if __name__ == '__main__':
    test_input = ['''
                 lekit（lazy and easy kit），
                 提供了项目中使用的绝大多数接口与工具，
                 在使得代码更加易读且明确的情况下，
                 还推动了项目耦合性的大幅降低与提高了极大程度的可维护以及扩展性。
                 经由lekit封装的LangChain等核心内容，
                 允许灵活地部署智能体并使用其服务，
                 并通过定制的prompt及其重封装类的模板构造合适的上下文
                 ''']
    core = SampleTestCore()
    result_file = core.run_with_list_of_str(test_input, tool_file("Runtime/Test/").must_exists_as_new())
    if result_file is None:
        print("Error: result file is None")
    else:
        print(f"Result:\n{result_file.data}")
        result_file.open('w')
        result_file.save()

