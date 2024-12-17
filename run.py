# coding=utf-8

from project.Core           import ProjectConfig
from project.sample_test    import *

if __name__ == '__main__':
    config = ProjectConfig()
    config.LogMessage("Project Start")
    
    sample_core = SampleTestCore("input.docx")
    sample_core.run()