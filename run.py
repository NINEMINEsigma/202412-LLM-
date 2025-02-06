# coding=utf-8

from lekit.lazy import *
from backend.Internal import *
from backend.sample_test import SampleTestCore

def run():
    core = SampleTestCore()
    result_file = core.run(
        GlobalConfig("Runtime/Test/"),
        tool_file("erp.docx"), 
        tool_file("Runtime/Test/").must_exists_path()
        )
    return result_file

if __name__ == '__main__':
    run()