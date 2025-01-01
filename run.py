# coding=utf-8

from lekit.Web.Core         import light_handler
from backend.Internal           import ProjectConfig
from backend.sample_test    import *

class ProjectCore:
    def __call__(self, file:tool_file):
        config = ProjectConfig()
        config.LogMessage(f"Current Target: {file}")
        sample_core = SampleTestCore(file)
        sample_core.run()
InjectCore = ProjectCore()

if __name__ == '__main__':
    config = ProjectConfig()
    config.LogMessage("Project Start")

    sample_core = SampleTestCore("input.docx")
    sample_core.run()