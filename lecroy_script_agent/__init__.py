"""
LeCroy Script Agent

自动生成 LeCroy PETrainer (.peg) 和 VSE (.pevs) 测试脚本的 AI Agent

支持协议:
- PCIe Physical Layer (LTSSM, Lane Break, RedoEQ, Hot Reset)
- PCIe Data Link Layer (TLP, DLLP, FLR, AER, Flow Control)
- CXL Link Layer (CXL.mem, Flit 打包, LL Credit)

使用示例:
    from agent import LeCroyScriptAgent
    
    agent = LeCroyScriptAgent()
    scripts = agent.generate_from_text("CXL MemRd 测试")
    
    # 保存脚本
    peg_file, pevs_file = scripts.save("./output")
"""

from .agent import LeCroyScriptAgent, TestCase, GeneratedScripts
from .agent import ProtocolType, TestScenario

__version__ = "1.0.0"
__all__ = [
    "LeCroyScriptAgent",
    "TestCase", 
    "GeneratedScripts",
    "ProtocolType",
    "TestScenario",
]
