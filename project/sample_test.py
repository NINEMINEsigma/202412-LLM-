# coding=utf-8

import typing
from docx import Document
import csv
from lekit.File.Core import get_extension_name, tool_file
from lekit.Str.Core import *

defined_names = {
    "Scene":    "Scene", 
    "Module":   "Module",
    "Operator": "Operator",
    "Expect":   "Expect"
}

def generate_test_cases(doc_texts:str) -> typing.List[str]:
    #return [
    #    {"场景或模块": "用户登录", "操作": "输入正确的用户名和密码", "预期状况": "登录成功"},
    #    {"场景或模块": "用户登录", "操作": "输入错误的用户名和密码", "预期状况": "显示错误消息"},
    #]
    
    pass

def read_word_document(file_path) -> str:
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def write_test_cases_to_word(test_cases, output_file_path):
    doc = Document()
    table = doc.add_table(rows=1, cols=3)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = r'当前场景或模块'
    hdr_cells[1].text = r'当前操作'
    hdr_cells[2].text = r'预期状况'
    
    for test_case in test_cases:
        row_cells = table.add_row().cells
        row_cells[0].text = test_case["场景或模块"]
        row_cells[1].text = test_case["操作"]
        row_cells[2].text = test_case["预期状况"]
    
    doc.save(output_file_path)
    
def write_test_cases_to_csv(test_cases, output_file_path):
    with open(output_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["当前场景或模块", "当前操作", "预期状况"])
        for test_case in test_cases:
            writer.writerow([test_case["场景或模块"], test_case["操作"], test_case["预期状况"]])

def sample_test_result_build(file_path:str='input.docx', output_file_path:str='output.csv'):
    # 读取设计文档
    design_document_text = read_word_document(file_path)
    
    # 使用LLM生成测试用例
    test_cases = generate_test_cases(design_document_text)
    
    # 将测试用例写入
    suffix = get_extension_name(output_file_path)
    if suffix == 'csv':
        write_test_cases_to_csv(test_cases, output_file_path)
    elif suffix == 'docx':
        write_test_cases_to_word(test_cases, output_file_path)
    else:
        raise ValueError(f"unsupport file type/suffix: {suffix}")

