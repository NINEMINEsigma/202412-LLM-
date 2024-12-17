# coding=utf-8

from project.sample_test import *
import io
import os
from docx import Document

def func(input_file_path:str='input.docx', output_file_path:str='output'):
    
    # 读取设计文档
    design_document_text = read_word_document(input_file_path)
    
    # 使用LLM生成测试用例
    test_cases = generate_test_cases(design_document_text)
    
    # 将测试用例写入新的csv文档
    write_test_cases_to_csv(test_cases, output_file_path+".csv")
    
    write_test_cases_to_word(test_cases, output_file_path+".docx")

if __name__ == '__main__':
    func()