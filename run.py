# coding=utf-8

from lekit.lazy import *
from backend.Internal import *
from backend.sample_test import SampleTestCore

def run():
    core = SampleTestCore()
    result_file = core.run(tool_file("input_x.docx"), tool_file("Runtime/Test/").must_exists_path())
    return result_file

def read_out():
    with tool_file("Runtime/Test/AutoRuntimePath.json") as file:
        data = file.load_as_json()
        print(data)

if __name__ == '__main__':
    #run()
    read_out()