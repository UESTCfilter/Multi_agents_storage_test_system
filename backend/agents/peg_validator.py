"""PEG 脚本语法校验器

基于 LeCroy PETrainer 语法规范，对生成的 PEG 脚本进行白名单检查。
"""

import re
from typing import List, Tuple

# PEG 有效指令白名单
VALID_PEG_COMMANDS = {
    "Link", "Packet", "Config", "Wait", "include",
    "Branch", "Proc", "Loop", "Repeat",
    "PCIeFlitMode", "CXL256BFlitMode",
    "SendLevel", "SendTraceEvent", "Log_Text",  # 这些实际上是 PEVS 的，但可能误出现在 PEG
}

# PEG 有效 Link 目标
VALID_LINK_TARGETS = {
    "L0", "L1", "L0s", "Loopback", "Disabled", "HotReset",
    "Recovery", "Detect", "PERST_Assert", "PERST_Deassert",
    "2_5", "5_0", "8_0", "16_0", "32_0",
    "x1", "x2", "x4", "x8", "x16",
    "RedoEQ", "SpeedChange",
}

# PEG 有效 Packet 类型
VALID_PACKET_TYPES = {
    "TLP", "DLLP", "CXL_Cache", "CXL_Mem", "CXL_LLCTRL",
    "SMBus", "OrderedSet", "Raw",
}

# PEG 有效 Config 类型
VALID_CONFIG_TYPES = {
    "General", "Link", "FCTx", "FCRx", "TLP", "AckNak",
    "Transactions", "Definitions", "ATS", "NVMe",
    "ErrorInjection", "CXL_Link", "CXL_ErrorInjection",
    "RawLtssm",
}


def validate_peg(content: str) -> List[dict]:
    """校验 PEG 脚本，返回错误列表
    
    每个错误是一个 dict:
        { "line": int, "text": str, "message": str, "severity": "error"|"warning" }
    """
    errors = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # 跳过空行和注释
        if not stripped or stripped.startswith(';') or stripped.startswith('#') or stripped.startswith('/*'):
            continue
        
        # 跳过多行注释中的行
        if '*/' in stripped and '/*' not in stripped:
            continue
        
        # 提取命令（等号前的部分）
        if '=' not in stripped:
            continue
        
        cmd_part = stripped.split('=')[0].strip()
        
        # 检查主命令是否在白名单
        if cmd_part not in VALID_PEG_COMMANDS:
            # 可能是赋值语句如 "Address = ..."，在 Packet = TLP { ... } 内部是合法的
            # 但如果它在顶层（不在 {} 内），可能是错误
            # 简单判断：如果前面有空格缩进，认为是参数，跳过
            if not line.startswith(' ') and not line.startswith('\t'):
                errors.append({
                    "line": i,
                    "text": stripped[:60],
                    "message": f"未知顶层指令: '{cmd_part}'",
                    "severity": "warning"
                })
        
        # Link 指令特殊检查
        if cmd_part == "Link":
            rhs = stripped.split('=', 1)[1].strip()
            target = rhs.split('{')[0].strip()
            if target not in VALID_LINK_TARGETS:
                # 可能是复合指令如 "Link = Recovery { Speed = 32_0 }"
                if target.split()[0] not in VALID_LINK_TARGETS | {"Recovery", "HotReset", "RedoEQ", "SpeedChange"}:
                    errors.append({
                        "line": i,
                        "text": stripped[:60],
                        "message": f"可疑的 Link 目标: '{target}'",
                        "severity": "warning"
                    })
        
        # Packet 指令特殊检查
        if cmd_part == "Packet":
            rhs = stripped.split('=', 1)[1].strip()
            pkt_type = rhs.split('{')[0].strip()
            if pkt_type not in VALID_PACKET_TYPES:
                errors.append({
                    "line": i,
                    "text": stripped[:60],
                    "message": f"可疑的 Packet 类型: '{pkt_type}'",
                    "severity": "warning"
                })
        
        # Config 指令特殊检查
        if cmd_part == "Config":
            rhs = stripped.split('=', 1)[1].strip()
            cfg_type = rhs.split('{')[0].strip()
            if cfg_type not in VALID_CONFIG_TYPES:
                errors.append({
                    "line": i,
                    "text": stripped[:60],
                    "message": f"可疑的 Config 类型: '{cfg_type}'",
                    "severity": "warning"
                })
        
        # 检查常见的错误语法
        if "PERST" in stripped and "PERST_Assert" not in stripped and "PERST_Deassert" not in stripped:
            errors.append({
                "line": i,
                "text": stripped[:60],
                "message": "PERST 必须使用 PERST_Assert / PERST_Deassert 两步操作",
                "severity": "error"
            })
        
        # 检查是否在代码块中写了自然语言（超过10个中文字符且不是注释）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', stripped)
        if len(chinese_chars) > 10 and not stripped.startswith(';') and not stripped.startswith('#') and not stripped.startswith('/*'):
            errors.append({
                "line": i,
                "text": stripped[:60],
                "message": f"代码行包含过多中文字符({len(chinese_chars)}个)，可能是推理文字混入了代码",
                "severity": "error"
            })
    
    return errors


def format_validation_report(errors: List[dict]) -> str:
    """将校验结果格式化为可读字符串"""
    if not errors:
        return "✅ PEG 语法校验通过，未发现明显问题。"
    
    lines = [f"⚠️ 发现 {len(errors)} 个问题:"]
    for e in errors:
        icon = "❌" if e["severity"] == "error" else "⚡"
        lines.append(f"  {icon} 第{e['line']}行: {e['message']}")
        lines.append(f"     {e['text']}")
    return "\n".join(lines)
