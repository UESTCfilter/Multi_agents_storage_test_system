#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LeCroy Script Agent - 自动生成 PETrainer/PEVS 测试脚本

基于模式库生成可直接运行的 .peg 训练脚本和 .pevs 验证脚本
支持: PCIe PL, PCIe DLL, CXL Link Layer

使用方法:
    python agent.py --test-desc "测试描述文本"
    python agent.py --file test_cases.txt
    python agent.py --interactive
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# 导入场景配置
SCENARIOS = {}
SCENARIO_MAPPING = {}

try:
    # 尝试相对导入（当作为包的一部分导入时）
    from .scenarios import SCENARIOS, SCENARIO_MAPPING
except ImportError:
    try:
        # 尝试绝对导入
        from lecroy_script_agent.scenarios import SCENARIOS, SCENARIO_MAPPING
    except ImportError:
        try:
            # 尝试直接导入（当在同级目录时）
            from scenarios import SCENARIOS, SCENARIO_MAPPING
        except ImportError:
            # 如果都失败，使用内嵌配置
            pass


class ProtocolType(Enum):
    """协议类型"""
    PCIE_PL = "pcie_pl"
    PCIE_DLL = "pcie_dll"
    CXL_MEM = "cxl_mem"
    CXL_CACHE = "cxl_cache"
    CXL_IO = "cxl_io"


class TestScenario(Enum):
    """测试场景"""
    LINK_UP = "link_up"
    LANE_BREAK = "lane_break"
    SPEED_CHANGE = "speed_change"
    HOT_RESET = "hot_reset"
    ASPM = "aspm"
    FLR = "flr"
    LINK_DISABLE = "link_disable"
    EQ_REDO = "eq_redo"
    AER_CHECK = "aer_check"
    FLOW_CONTROL = "flow_control"
    ACK_NAK = "ack_nak"
    SURPRISE_DOWN = "surprise_down"
    FEATURE_EXCHANGE = "feature_exchange"
    CXL_MEM_RD = "cxl_mem_rd"
    CXL_MEM_WR = "cxl_mem_wr"
    CXL_FLIT_PACK = "cxl_flit_pack"
    CXL_LL_CREDIT = "cxl_ll_credit"
    CXL_CACHE_BASIC = "cxl_cache_basic"
    CXL_IO_CFG = "cxl_io_cfg"
    IDE_KEY_EXCHANGE = "ide_key_exchange"
    GEN6_FLIT = "gen6_flit"
    CXL_256B_FLIT = "cxl_256b_flit"
    LMR = "lmr"
    PM_L1SUB = "pm_l1sub"
    CXL_CACHE_DIRTY_EVICT = "cxl_cache_dirty_evict"
    ATOMIC_OPS = "atomic_ops"
    TL_TLP_BASIC = "tl_tlp_basic"
    TL_ECRC = "tl_ecrc"
    TL_TPH_ATS = "tl_tph_ats"
    TL_VENDOR_MSG = "tl_vendor_msg"
    TL_CPL_TIMEOUT = "tl_cpl_timeout"


@dataclass
class TestCase:
    """测试用例定义"""
    name: str
    description: str
    protocol: ProtocolType
    scenario: TestScenario
    steps: List[Dict] = field(default_factory=list)
    expected_results: List[str] = field(default_factory=list)
    config: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "protocol": self.protocol.value,
            "scenario": self.scenario.value,
            "steps": self.steps,
            "expected_results": self.expected_results,
            "config": self.config
        }


@dataclass
class GeneratedScripts:
    """生成的脚本"""
    peg_content: str
    pevs_content: str
    test_name: str
    protocol: str
    scenario: str
    
    def save(self, output_dir: str = "./output") -> Tuple[str, str]:
        """保存脚本到文件"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 清理文件名
        safe_name = re.sub(r'[^\w\s-]', '', self.test_name).strip().replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        peg_file = output_path / f"{safe_name}_{timestamp}.peg"
        pevs_file = output_path / f"{safe_name}_{timestamp}.pevs"
        
        peg_file.write_text(self.peg_content, encoding='utf-8')
        pevs_file.write_text(self.pevs_content, encoding='utf-8')
        
        return str(peg_file), str(pevs_file)


class LeCroyScriptAgent:
    """LeCroy 脚本生成 Agent"""
    
    def __init__(self, scenarios_config: Dict = None):
        self.scenarios = scenarios_config or SCENARIOS
        self.mapping = SCENARIO_MAPPING
    
    def detect_scenario(self, description: str) -> str:
        """
        从描述中检测场景类型
        
        Returns:
            场景 key (如 "pcie_pl_link_up")
        """
        desc_lower = description.lower()
        
        # 按优先级匹配关键词
        for keyword, scenario_key in sorted(self.mapping.items(), key=lambda x: -len(x[0])):
            if keyword in desc_lower:
                return scenario_key
        
        # 默认场景
        return "pcie_pl_link_up"
    
    def parse_test_case(self, test_description: str, name: str = None) -> TestCase:
        """解析测试用例"""
        scenario_key = self.detect_scenario(test_description)
        scenario_config = self.scenarios.get(scenario_key, {})
        
        # 检测协议类型
        protocol = self._detect_protocol(test_description, scenario_key)
        
        # 提取测试名称
        test_name = name or self._extract_name(test_description)
        
        # 映射 scenario_key 到 TestScenario
        scenario_value = self._map_scenario_key(scenario_key)
        
        return TestCase(
            name=test_name,
            description=test_description,
            protocol=protocol,
            scenario=TestScenario(scenario_value),
            steps=self._extract_steps(test_description),
            expected_results=self._extract_expected(test_description)
        )
    
    def _map_scenario_key(self, scenario_key: str) -> str:
        """将场景 key 映射到 TestScenario 值"""
        mapping = {
            "pcie_pl_link_up": "link_up",
            "pcie_pl_lane_break": "lane_break",
            "pcie_pl_redo_eq": "eq_redo",
            "pcie_pl_hot_reset": "hot_reset",
            "pcie_pl_speed_change": "speed_change",
            "pcie_pl_aspm": "aspm",
            "pcie_dll_flr": "flr",
            "pcie_dll_link_disable": "link_disable",
            "pcie_dll_flow_control": "flow_control",
            "pcie_dll_aer_check": "aer_check",
            "pcie_dll_ack_nak": "ack_nak",
            "pcie_dll_surprise_down": "surprise_down",
            "pcie_dll_feature_exchange": "feature_exchange",
            "cxl_mem_basic_rd": "cxl_mem_rd",
            "cxl_mem_multi_req": "cxl_flit_pack",
            "cxl_ll_credit": "cxl_ll_credit",
            "cxl_cache_basic": "cxl_cache_basic",
            "cxl_io_cfg_access": "cxl_io_cfg",
            "pcie_ide_key_exchange": "ide_key_exchange",
            "pcie_pl_gen6_flit": "gen6_flit",
            "cxl_256b_flit": "cxl_256b_flit",
            "cxl_mem_basic_wr": "cxl_mem_wr",
            "pcie_pl_lmr": "lmr",
            "pcie_pl_pm_l1sub": "pm_l1sub",
            "cxl_cache_dirty_evict": "cxl_cache_dirty_evict",
            "pcie_dll_atomic_ops": "atomic_ops",
            "pcie_tl_tlp_basic": "tl_tlp_basic",
            "pcie_tl_ecrc": "tl_ecrc",
            "pcie_tl_tph_ats": "tl_tph_ats",
            "pcie_tl_vendor_msg": "tl_vendor_msg",
            "pcie_tl_completion_timeout": "tl_cpl_timeout",
        }
        return mapping.get(scenario_key, "link_up")
    
    def _detect_protocol(self, desc: str, scenario_key: str) -> ProtocolType:
        """检测协议类型"""
        if scenario_key.startswith("cxl_"):
            return ProtocolType.CXL_MEM
        elif scenario_key.startswith("pcie_dll_"):
            return ProtocolType.PCIE_DLL
        else:
            return ProtocolType.PCIE_PL
    
    def _extract_name(self, desc: str) -> str:
        """提取测试名称"""
        # 使用描述的第一行或前50个字符
        lines = [l.strip() for l in desc.split('\n') if l.strip()]
        if lines:
            name = lines[0][:50]
        else:
            name = "Unnamed_Test"
        
        # 清理特殊字符
        name = re.sub(r'[^\w\s\-_]', '', name)
        return name.strip() or "Unnamed_Test"
    
    def _extract_steps(self, desc: str) -> List[Dict]:
        """提取测试步骤"""
        steps = []
        
        # 匹配多种步骤格式
        patterns = [
            r'步骤\s*(\d+)[:：]\s*([^\n]+)',  # 步骤 1: xxx
            r'(\d+)\.\s+([^\n]+)',              # 1. xxx
            r'step\s*(\d+)[:：]\s*([^\n]+)',   # Step 1: xxx
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, desc, re.IGNORECASE)
            for num, step_desc in matches:
                steps.append({
                    "step_num": int(num),
                    "description": step_desc.strip()
                })
        
        # 去重并排序
        seen = set()
        unique_steps = []
        for step in sorted(steps, key=lambda x: x["step_num"]):
            if step["step_num"] not in seen:
                seen.add(step["step_num"])
                unique_steps.append(step)
        
        return unique_steps
    
    def _extract_expected(self, desc: str) -> List[str]:
        """提取预期结果"""
        expected = []
        
        patterns = [
            r'(?:预期结果|expected|预期)[:：]\s*([^\n]+)',
            r'预期[:：]\s*([^\n]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, desc, re.IGNORECASE)
            expected.extend([m.strip() for m in matches])
        
        return expected
    
    def generate(self, test_case: TestCase) -> GeneratedScripts:
        """生成脚本"""
        # 反向查找场景模板
        scenario_key = None
        reverse_mapping = {
            "link_up": "pcie_pl_link_up",
            "lane_break": "pcie_pl_lane_break",
            "eq_redo": "pcie_pl_redo_eq",
            "hot_reset": "pcie_pl_hot_reset",
            "speed_change": "pcie_pl_speed_change",
            "aspm": "pcie_pl_aspm",
            "flr": "pcie_dll_flr",
            "link_disable": "pcie_dll_link_disable",
            "flow_control": "pcie_dll_flow_control",
            "aer_check": "pcie_dll_aer_check",
            "ack_nak": "pcie_dll_ack_nak",
            "surprise_down": "pcie_dll_surprise_down",
            "feature_exchange": "pcie_dll_feature_exchange",
            "cxl_mem_rd": "cxl_mem_basic_rd",
            "cxl_mem_wr": "cxl_mem_basic_rd",
            "cxl_flit_pack": "cxl_mem_multi_req",
            "cxl_ll_credit": "cxl_ll_credit",
            "cxl_cache_basic": "cxl_cache_basic",
            "cxl_io_cfg_access": "cxl_io_cfg",
            "pcie_ide_key_exchange": "ide_key_exchange",
            "pcie_pl_gen6_flit": "gen6_flit",
            "cxl_256b_flit": "cxl_256b_flit",
            "cxl_mem_basic_wr": "cxl_mem_wr",
            "pcie_pl_lmr": "lmr",
            "pcie_pl_pm_l1sub": "pm_l1sub",
            "cxl_cache_dirty_evict": "cxl_cache_dirty_evict",
            "pcie_dll_atomic_ops": "atomic_ops",
            "pcie_tl_tlp_basic": "tl_tlp_basic",
            "pcie_tl_ecrc": "tl_ecrc",
            "pcie_tl_tph_ats": "tl_tph_ats",
            "pcie_tl_vendor_msg": "tl_vendor_msg",
            "pcie_tl_completion_timeout": "tl_cpl_timeout",
        }
        
        scenario_key = reverse_mapping.get(test_case.scenario.value, "pcie_pl_link_up")
        
        template = self.scenarios.get(scenario_key, {})
        
        # 生成 PEG
        peg_content = self._generate_peg(test_case, template.get("peg_template", ""))
        
        # 生成 PEVS
        pevs_content = self._generate_pevs(test_case, template.get("pevs_template", ""))
        
        return GeneratedScripts(
            peg_content=peg_content,
            pevs_content=pevs_content,
            test_name=test_case.name,
            protocol=test_case.protocol.value,
            scenario=test_case.scenario.value
        )
    
    def _generate_header(self, test_case: TestCase) -> str:
        """生成文件头部注释"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""######################################################################################################
# {test_case.name}
# {test_case.description[:80]}
#
# 协议类型: {test_case.protocol.value}
# 测试场景: {test_case.scenario.value}
# 生成时间: {timestamp}
# 生成工具: LeCroy Script Agent
######################################################################################################
"""
    
    def _generate_peg(self, test_case: TestCase, template: str) -> str:
        """生成 PEG 训练脚本"""
        header = self._generate_header(test_case)
        
        # 根据用例描述识别触发条件
        trigger_dllp = self._detect_trigger_dllp(test_case.description)
        
        # 替换模板变量（使用 replace 避免模板中其他 { } 被 format 解析）
        content = template.replace("{trigger_dllp}", trigger_dllp)
        
        return header + "\n" + content
    
    def _detect_trigger_dllp(self, description: str) -> str:
        """检测触发条件的 DLLP 类型"""
        desc_lower = description.lower()
        
        # 检查 InitFC1/Init FC1
        if any(kw in desc_lower for kw in ['initfc1', 'init fc1', 'init_fc1']):
            return "InitFC1_P"
        
        # 检查 InitFC2
        if any(kw in desc_lower for kw in ['initfc2', 'init fc2', 'init_fc2']):
            return "InitFC2_P"
        
        # 检查 UpdateFC
        if any(kw in desc_lower for kw in ['updatefc', 'update fc', 'update_fc']):
            return "UpdateFC_P"
        
        # 默认 Feature DLLP
        return "Data_Link_Feature"
    
    def _generate_pevs(self, test_case: TestCase, template: str) -> str:
        """生成 PEVS 验证脚本"""
        header = self._generate_header(test_case)
        
        # 标准 include
        includes = """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "%s";

%%include "VSTools.inc"
""" % test_case.name[:50]
        
        # 根据协议添加特定 include
        if test_case.protocol == ProtocolType.PCIE_PL:
            includes += '%include "physical_layer_common.inc"\n'
        elif test_case.protocol == ProtocolType.PCIE_DLL:
            includes += '%include "data_link_layer_common.inc"\n'
        elif test_case.protocol == ProtocolType.CXL_MEM:
            includes += '%include "data_link_layer_common.inc"\n'
            includes += '%include "cxl_common.inc"\n'
        
        return header + includes + "\n" + template
    
    def generate_from_text(self, test_description: str, name: str = None) -> GeneratedScripts:
        """从文本直接生成"""
        test_case = self.parse_test_case(test_description, name)
        return self.generate(test_case)
    
    def batch_generate(self, test_cases: List[Tuple[str, Optional[str]]], output_dir: str = "./output") -> List[GeneratedScripts]:
        """批量生成"""
        results = []
        
        for desc, name in test_cases:
            try:
                scripts = self.generate_from_text(desc, name)
                peg_file, pevs_file = scripts.save(output_dir)
                print(f"✓ 生成成功: {scripts.test_name}")
                print(f"  PEG:  {peg_file}")
                print(f"  PEVS: {pevs_file}")
                results.append(scripts)
            except Exception as e:
                print(f"✗ 生成失败: {name or desc[:30]}... 错误: {e}")
        
        return results
    
    def list_scenarios(self) -> None:
        """列出支持的场景"""
        print("\n支持的测试场景:\n")
        print("-" * 60)
        
        categories = {
            "PCIe Physical Layer": [],
            "PCIe Data Link Layer": [],
            "CXL Link Layer": []
        }
        
        for key, config in self.scenarios.items():
            desc = config.get("description", "No description")
            if key.startswith("pcie_pl_"):
                categories["PCIe Physical Layer"].append((key, desc))
            elif key.startswith("pcie_dll_"):
                categories["PCIe Data Link Layer"].append((key, desc))
            elif key.startswith("cxl_"):
                categories["CXL Link Layer"].append((key, desc))
        
        for category, items in categories.items():
            if items:
                print(f"\n【{category}】")
                for key, desc in sorted(items):
                    print(f"  {key:<30} - {desc}")
        
        print("\n" + "-" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="LeCroy Script Agent - 自动生成 PETrainer/PEVS 测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --test-desc "CXL MemRd 基本测试"
  %(prog)s --file test_cases.txt --output ./scripts
  %(prog)s --interactive
  %(prog)s --list
        """
    )
    
    parser.add_argument("--test-desc", "-t", help="测试描述文本")
    parser.add_argument("--name", "-n", help="测试名称")
    parser.add_argument("--file", "-f", help="包含多个测试用例的文件")
    parser.add_argument("--output", "-o", default="./output", help="输出目录 (默认: ./output)")
    parser.add_argument("--list", "-l", action="store_true", help="列出支持的测试场景")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式模式")
    parser.add_argument("--save-meta", "-m", action="store_true", help="保存测试用例元数据")
    
    args = parser.parse_args()
    
    agent = LeCroyScriptAgent()
    
    if args.list:
        agent.list_scenarios()
        return
    
    if args.interactive:
        print("\n=== LeCroy Script Agent 交互式模式 ===\n")
        print("输入测试描述 (空行结束):")
        
        lines = []
        while True:
            line = input("> ")
            if not line.strip():
                break
            lines.append(line)
        
        if lines:
            test_desc = "\n".join(lines)
            print("\n生成中...")
            
            scripts = agent.generate_from_text(test_desc)
            peg_file, pevs_file = scripts.save(args.output)
            
            print(f"\n✓ 生成成功!")
            print(f"  协议: {scripts.protocol}")
            print(f"  场景: {scripts.scenario}")
            print(f"  PEG:  {peg_file}")
            print(f"  PEVS: {pevs_file}")
        return
    
    if args.test_desc:
        scripts = agent.generate_from_text(args.test_desc, args.name)
        peg_file, pevs_file = scripts.save(args.output)
        
        print(f"✓ 生成成功: {scripts.test_name}")
        print(f"  PEG:  {peg_file}")
        print(f"  PEVS: {pevs_file}")
        
        if args.save_meta:
            meta_file = Path(peg_file).with_suffix('.json')
            test_case = agent.parse_test_case(args.test_desc, args.name)
            meta_file.write_text(json.dumps(test_case.to_dict(), indent=2, ensure_ascii=False))
            print(f"  META: {meta_file}")
        
        return
    
    if args.file:
        # 从文件读取多个测试用例
        content = Path(args.file).read_text(encoding='utf-8')
        
        # 简单解析：按空行分隔
        test_cases = []
        current_desc = []
        current_name = None
        
        for line in content.split('\n'):
            if line.startswith('#'):
                if current_desc:
                    test_cases.append(("\n".join(current_desc), current_name))
                current_name = line[1:].strip()
                current_desc = []
            elif line.strip() == '---':
                if current_desc:
                    test_cases.append(("\n".join(current_desc), current_name))
                current_desc = []
                current_name = None
            else:
                current_desc.append(line)
        
        if current_desc:
            test_cases.append(("\n".join(current_desc), current_name))
        
        print(f"从文件加载 {len(test_cases)} 个测试用例\n")
        agent.batch_generate(test_cases, args.output)
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()
