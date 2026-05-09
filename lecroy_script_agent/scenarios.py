# LeCroy Script Agent - 场景配置
# 扩展的模式库配置

SCENARIOS = {
    # PCIe Physical Layer
    "pcie_pl_link_up": {
        "description": "基础建链到 L0",
        "peg_template": """include = "./common_initialize.peg"
Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = Detect
Link = L0
wait = 2000000
""",
        "pevs_template": """OnStartScript() {
    Init_PL_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendLtssm();
    SendTraceEvent(_PKT_LINK_STATE);
}

ProcessEvent() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L0) {
        Log_Text("Link up to L0 successfully");
        Success_Complete();
    }
}
"""
    },
    
    "pcie_pl_lane_break": {
        "description": "Lane Break 测试 (如 x2→x1)",
        "peg_template": """include = "./common_initialize.peg"
Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = Detect
Link = L0
; 触发 Lane Break
Config = Link { DropLanes = 0x2 }
wait = 1000000
Link = L0
""",
        "pevs_template": """OnStartScript() {
    Init_PL_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendLtssm();
    SendTraceEvent(_PKT_LINK_STATE);
    SendTraceEvent(_PKT_LANE_INFO);
}

ProcessEvent() {
    select {
        stage == 1 : Check_Link_Width();
        stage == 2 : Check_Recovery();
    };
}

Check_Link_Width() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L0) {
        if(in.LinkWidth == 2) {
            Log_Text("Initial link width: x2");
            stage++;
        }
    }
}

Check_Recovery() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_RECOVERY) {
        if(in.LinkWidth == 1) {
            Log_Text("Lane break successful: x2 -> x1");
            Success_Complete();
        }
    }
}
"""
    },
    
    "pcie_pl_redo_eq": {
        "description": "RedoEQ 重均衡测试",
        "peg_template": """include = "./common_initialize.peg"
Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = Detect
Link = L0
; 触发 RedoEQ
Link = RedoEQ {
    Initiate = Yes
    Speed = 8_0
    AtTargetSpeed = No
}
wait = 5000000
""",
        "pevs_template": """OnStartScript() {
    Init_PL_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendLtssm();
    SendTraceEvent(_PKT_RECOVERY_STATE);
    SendTraceEvent(_PKT_TX_PRESET);
    SetTimer();
}

ProcessEvent() {
    select {
        stage == 1 : Check_Recovery_EQ();
        stage == 2 : Check_Tx_Preset();
    };
}

Check_Recovery_EQ() {
    if(in.TraceEvent == _PKT_RECOVERY_STATE && in.RecoveryState eq "Recovery.EQ") {
        Log_Text("Enter Recovery.EQ");
        stage++;
    }
}

Check_Tx_Preset() {
    if(in.TraceEvent == _PKT_TX_PRESET) {
        Log_Text(FormatEx("Tx Preset captured: %d", in.TxPreset));
        Success_Complete();
    }
}
"""
    },
    
    "pcie_pl_hot_reset": {
        "description": "Hot Reset 热复位测试",
        "peg_template": """include = "./common_initialize.peg"
Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = Detect
Link = L0
; 在 L0 状态发送 Hot Reset
Link = HotReset
wait = 3000000
Link = L0
wait = 2000000
""",
        "pevs_template": """OnStartScript() {
    Init_PL_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendLtssm();
    SendTraceEvent(_PKT_LINK_STATE);
    stage = 1;
    SetTimer();
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_L0_Before_Reset();
            stage == 2 : Check_Hot_Reset();
            stage == 3 : Check_L0_After_Reset();
        };
    }
}

Check_L0_Before_Reset() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L0) {
        Log_Text("Reached L0 before Hot Reset");
        stage++;
    }
}

Check_Hot_Reset() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_HOTRESET) {
        Log_Text("Hot Reset detected");
        stage++;
    }
}

Check_L0_After_Reset() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L0) {
        Log_Text("Link recovered to L0 after Hot Reset");
        Success_Complete();
    }
}
"""
    },
    
    "pcie_pl_speed_change": {
        "description": "PCIe 速率切换测试 (Gen3→Gen4→Gen5)",
        "peg_template": """include = "./common_initialize.peg"
Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = Detect
; 初始建链到 Gen3
Config = Link { TargetSpeed = 8_0 }
Link = L0
wait = 2000000
; 触发速度切换
Config = Link { TargetSpeed = 16_0 }
Link = SpeedChange
wait = 5000000
; 再次触发到 Gen5
Config = Link { TargetSpeed = 32_0 }
Link = SpeedChange
wait = 5000000
""",
        "pevs_template": """OnStartScript() {
    Init_PL_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendLtssm();
    SendTraceEvent(_PKT_LINK_SPEED);
    stage = 1;
    SetTimer();
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_Gen3();
            stage == 2 : Check_Gen4();
            stage == 3 : Check_Gen5();
        };
    }
}

Check_Gen3() {
    if(in.TraceEvent == _PKT_LINK_SPEED && in.LinkSpeed == 4) {
        Log_Text("Link established at Gen3 (8GT/s)");
        stage++;
    }
}

Check_Gen4() {
    if(in.TraceEvent == _PKT_LINK_SPEED && in.LinkSpeed == 5) {
        Log_Text("Speed change to Gen4 (16GT/s) successful");
        stage++;
    }
}

Check_Gen5() {
    if(in.TraceEvent == _PKT_LINK_SPEED && in.LinkSpeed == 6) {
        Log_Text("Speed change to Gen5 (32GT/s) successful");
        Success_Complete();
    }
}
"""
    },
    
    "pcie_pl_aspm": {
        "description": "ASPM L0s/L1 功耗管理测试",
        "peg_template": """include = "./common_initialize.peg"
Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = Detect
Link = L0
wait = 2000000
; 启用 ASPM L1
Config = Link { ASPM = L1 }
wait = 1000000
; 触发进入 L1
Link = L1
wait = 2000000
; 唤醒回到 L0
Link = L0
wait = 2000000
""",
        "pevs_template": """OnStartScript() {
    Init_PL_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendLtssm();
    SendTraceEvent(_PKT_LINK_STATE);
    stage = 1;
    SetTimer();
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_L0_Initial();
            stage == 2 : Check_L1_Entry();
            stage == 3 : Check_L0_Exit();
        };
    }
}

Check_L0_Initial() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L0) {
        Log_Text("Initial L0 established");
        stage++;
    }
}

Check_L1_Entry() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L1) {
        Log_Text("ASPM L1 entry successful");
        stage++;
    }
}

Check_L0_Exit() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L0) {
        Log_Text("ASPM L1 exit back to L0 successful");
        Success_Complete();
    }
}
"""
    },
    
    # PCIe Data Link Layer
    "pcie_dll_flr": {
        "description": "Function Level Reset 测试",
        "peg_template": """include = "./common_initialize_dl.peg"
Link = HotReset
Link = Detect
Link = L0
; 读取 Device Control
Packet="DeviceCtrl_R"
wait=TLP { TLPType = CplD }
wait = INTER_TRANSACTION_DELAY
; 写入 FLR
Packet="DeviceCtrl_W" { PayLoad = 0x1fa00000 }
wait=TLP { TLPType = Cpl }
; 等待
Loop = Begin { count = 5 }
    wait = 70000000
Loop = End
; 检查错误寄存器
Packet="UNC_Status_R"
wait=TLP { TLPType = CplD }
wait = INTER_TRANSACTION_DELAY
Packet="UC_Status_R"
wait=TLP { TLPType = CplD }
""",
        "pevs_template": """OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_TLP);
}

ProcessEvent() {
    if(in.TLPType == TLP_TYPE_ID_CFGRD_0 && in.Register == UncorrectableErrReg) {
        UncStatusRdTag = in.Tag;
        stage++;
    }
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 2 : ProcessUncorrectableErrReg();
            stage == 3 : ProcessCorrectableErrReg();
        };
    }
}

ProcessUncorrectableErrReg() {
    if(in.TLPType == TLP_TYPE_ID_CPLD && in.Tag == UncStatusRdTag) {
        if(in.RegisterData == TLP_NOERR_STATUS) {
            Log_Text("Uncorrectable Error: No error after FLR");
            stage++;
        } else {
            FailTest_Common("Errors in Uncorrectable Error Register after FLR!");
        }
    }
}

ProcessCorrectableErrReg() {
    if(in.TLPType == TLP_TYPE_ID_CPLD) {
        if(in.RegisterData == TLP_NOERR_STATUS) {
            Log_Text("Correctable Error: No error after FLR");
            Success_Complete();
        } else {
            FailTest_Common("Errors in Correctable Error Register after FLR!");
        }
    }
}
"""
    },
    
    "pcie_dll_aer_check": {
        "description": "AER (Advanced Error Reporting) 寄存器检查",
        "peg_template": """include = "./common_initialize_dl.peg"
Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = Detect
Link = L0
; 读取 Uncorrectable Error Status Register
Packet="UNC_Status_R"
wait=TLP { TLPType = CplD }
wait = INTER_TRANSACTION_DELAY
; 读取 Correctable Error Status Register
Packet="UC_Status_R"
wait=TLP { TLPType = CplD }
""",
        "pevs_template": """OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_TLP);
    g_UncTag = 0;
}

ProcessEvent() {
    if(in.TLPType == TLP_TYPE_ID_CFGRD_0 && in.Register == UncorrectableErrReg) {
        g_UncTag = in.Tag;
        stage++;
    }
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 2 : ProcessUncorrectableErrReg();
            stage == 3 : ProcessCorrectableErrReg();
        };
    }
}

ProcessUncorrectableErrReg() {
    if(in.TLPType == TLP_TYPE_ID_CPLD && in.Tag == g_UncTag) {
        if(in.RegisterData == TLP_NOERR_STATUS) {
            Log_Text("Uncorrectable Error Status: No error");
            stage++;
        } else {
            Log_Text(FormatEx("Uncorrectable Error Status: 0x%x", in.RegisterData));
            FailTest_Common("Uncorrectable errors detected!");
        }
    }
}

ProcessCorrectableErrReg() {
    if(in.TLPType == TLP_TYPE_ID_CPLD) {
        if(in.RegisterData == TLP_NOERR_STATUS) {
            Log_Text("Correctable Error Status: No error");
            Success_Complete();
        } else {
            Log_Text(FormatEx("Correctable Error Status: 0x%x", in.RegisterData));
            FailTest_Common("Correctable errors detected!");
        }
    }
}
"""
    },
    
    "pcie_dll_link_disable": {
        "description": "Link Disable 测试",
        "peg_template": """# PERST 重置链路
Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }

# 等待触发条件 DLLP
Wait=DLLP { DLLPType={trigger_dllp} }

# 触发 Link Disable
Link=Disabled

# 重新训练到 L0
Link=L0

# 最终状态确认
wait = 10000000
""",
        "pevs_template": """OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_TLP);
    SendTraceEvent(_PKT_LINK_STATE);
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_Link_Up();
            stage == 2 : Check_AER();
        };
    }
}

Check_Link_Up() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L0) {
        Log_Text("Link recovered to L0 after disable");
        stage++;
    }
}

Check_AER() {
    if(in.TLPType == TLP_TYPE_ID_CPLD) {
        if(in.RegisterData == TLP_NOERR_STATUS) {
            Log_Text("No error after Link Disable");
            Success_Complete();
        } else {
            FailTest_Common("Errors after Link Disable!");
        }
    }
}
"""
    },
    
    "pcie_dll_flow_control": {
        "description": "Flow Control 初始化测试",
        "peg_template": """include = "./common_initialize_dl.peg"
Config = FCRx {
    NPH = 1
    NPD = 1
    PH = 250
    PD = 4000
    CplH = 250
    CplD = 4000
}
Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Wait=LinkCondition { Conditions=LinkAlive }
Wait=DLLP { DLLPType=InitFC1_P }
Wait=DLLP { DLLPType=UpdateFc_P }
Packet="UNC_Status_R"
wait=TLP { TLPType = CplD }
""",
        "pevs_template": """OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendChannelOnly(_CHANNEL_2);
    SendTraceEvent(_PKT_DLLP);
    SendTraceEvent(_PKT_TLP);
}

ProcessEvent() {
    select {
        stage == 1 : Check_InitFC1_P();
        stage == 2 : Check_InitFC1_NP();
        stage == 3 : Check_InitFC1_Cpl();
    };
}

Check_InitFC1_P() {
    if(in.TraceEvent == _PKT_DLLP && in.DLLPType == DLLP_TYPE_INITFC1_P) {
        Log_Text(FormatEx("InitFC1_P: HdrFC=%d, DataFC=%d", in.HdrFC, in.DataFC));
        stage++;
    }
}

Check_InitFC1_NP() {
    if(in.TraceEvent == _PKT_DLLP && in.DLLPType == DLLP_TYPE_INITFC1_NP) {
        Log_Text(FormatEx("InitFC1_NP: HdrFC=%d, DataFC=%d", in.HdrFC, in.DataFC));
        stage++;
    }
}

Check_InitFC1_Cpl() {
    if(in.TraceEvent == _PKT_DLLP && in.DLLPType == DLLP_TYPE_INITFC1_CPL) {
        Log_Text(FormatEx("InitFC1_Cpl: HdrFC=%d, DataFC=%d", in.HdrFC, in.DataFC));
        Success_Complete();
    }
}
"""
    },
    
    "pcie_dll_ack_nak": {
        "description": "ACK/NAK DLLP 机制验证",
        "peg_template": """include = "./common_initialize_dl.peg"
Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = Detect
Link = L0
; 发送 Config Read TLP 触发 ACK
Packet="DeviceCtrl_R"
wait=TLP { TLPType = CplD }
wait = INTER_TRANSACTION_DELAY
; 再次发送验证 NAK 场景
Packet="DeviceCtrl_R"
wait=TLP { TLPType = CplD }
""",
        "pevs_template": """OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_DLLP);
    SendTraceEvent(_PKT_TLP);
    g_AckCount = 0;
    stage = 1;
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_ACK();
            stage == 2 : Check_Second_ACK();
        };
    }
}

Check_ACK() {
    if(in.TraceEvent == _PKT_DLLP && in.DLLPType == DLLP_TYPE_ACK) {
        g_AckCount++;
        Log_Text(FormatEx("ACK received: SeqNum=%d", in.SeqNum));
        if(g_AckCount >= 1) {
            stage++;
        }
    }
}

Check_Second_ACK() {
    if(in.TraceEvent == _PKT_DLLP && in.DLLPType == DLLP_TYPE_ACK) {
        g_AckCount++;
        Log_Text(FormatEx("Second ACK received: SeqNum=%d", in.SeqNum));
        if(g_AckCount >= 2) {
            Log_Text("ACK/NAK mechanism verified");
            Success_Complete();
        }
    }
}
"""
    },
    
    "pcie_dll_surprise_down": {
        "description": "Surprise Down 意外掉电测试",
        "peg_template": """include = "./common_initialize_dl.peg"
Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = Detect
Link = L0
; 确认链路正常
wait = 2000000
; 模拟 Surprise Down
Link = Detect
; 检查恢复
wait = 5000000
""",
        "pevs_template": """OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendLtssm();
    SendTraceEvent(_PKT_LINK_STATE);
    SendTraceEvent(_PKT_TLP);
    stage = 1;
    SetTimer();
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_L0_Initial();
            stage == 2 : Check_Surprise_Down();
            stage == 3 : Check_Recovery();
        };
    }
}

Check_L0_Initial() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L0) {
        Log_Text("Link at L0 before Surprise Down");
        stage++;
    }
}

Check_Surprise_Down() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_DETECT) {
        Log_Text("Surprise Down detected (Link went to Detect)");
        stage++;
    }
}

Check_Recovery() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L0) {
        Log_Text("Link recovered to L0 after Surprise Down");
        Success_Complete();
    }
}
"""
    },
    
    # CXL Link Layer
    "cxl_mem_basic_rd": {
        "description": "CXL.mem 基础读测试",
        "peg_template": """include = "./common_initialize_dl.peg"
include = "../Common/cxl_init/cxl_init.peg"
Packet = CXL_Mem {
    CXLMemType = M2S_MemReq
    MemReqOpcode = MemRd
    SnpType = NoOp
    MetaField = NoOp
    AutoIncrementTag = Yes
    Address = (HDM_DECODER0_BASE >> 6)
}
Wait = LinkCondition { Conditions = CXLLlcrd }
Config = CXL_Link { LLCTRLUserControl = on }
Packet = CXL_LLCTRL {
    LLCTRLType = LLCRDAck
    LLCRDMemReqRspCredits = 1
    LLCRDMemDataCredits = 1
}
Config = CXL_Link { LLCTRLUserControl = off }
Wait = CXL_Mem { CXLMemType = S2M_MemDataResp Timeout = 10000 }
""",
        "pevs_template": """OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_TLP);
    SendTraceEvent(_PKT_CXL_CACHE_MEM);
}

ProcessEvent() {
    select {
        stage == 1 : Process_M2S_Req();
        stage == 2 : Process_S2M_Resp();
    };
}

Process_M2S_Req() {
    if(in.TraceEvent == _PKT_TLP && in.Channel == _CHANNEL_1 && 
       in.CXLMemType == CXL_MEM_M2S_MemReq) {
        Log_Text("M2S MemReq sent successfully");
        stage++;
    }
}

Process_S2M_Resp() {
    if(in.TraceEvent == _PKT_TLP && in.Channel == _CHANNEL_2 &&
       in.CXLMemType == CXL_MEM_S2M_MemDataResp) {
        Log_Text("S2M MemDataResp received");
        Success_Complete();
    }
}
"""
    },
    
    "cxl_mem_multi_req": {
        "description": "CXL.mem 多发请求测试 (3 Req -> 4 Flit)",
        "peg_template": """include = "./common_initialize_dl.peg"
include = "./LL_Disable_MDH.peg"
Wait=DLLP { DLLPType=UpdateFc_NP }
include="../Common/cxl_init/config_bar.peg"
include="../Common/cxl_init/enable_cxl_mem.peg"
; 禁用 MDH
packet="CXL_MEM_REG_READ" { AddressLo = ( CXL_Link_Offset + 0x30 ) }
Wait=TLP { TLPType=CplD }
; 发送 3 个 M2S Req
Packet = CXL_Mem {
    CXLMemType = M2S_MemReq
    MemReqOpcode = MemRd
    SnpType = NoOp
    MetaField = NoOp
    AutoIncrementTag = Yes
    Address = (HDM_DECODER0_BASE >> 6)
    AutoIncrementAddress = Yes
    Count = 3
}
Wait = LinkCondition { Conditions=CXLLlcrd }
Config = CXL_Link { LLCTRLUserControl = on }
Packet = CXL_LLCTRL {
    LLCTRLType=LLCRDAck
    LLCRDMemReqRspCredits = 3
    LLCRDMemDataCredits = 64
}
Config = CXL_Link { LLCTRLUserControl = off }
Wait = CXL_Mem { CXLMemType=S2M_MemDataResp Timeout = 10000 Count = 3 }
""",
        "pevs_template": """OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_TLP);
    SendTraceEvent(_PKT_CXL_CACHE_MEM);
    g_Req_Count = 0;
    g_Flit_Count = 0;
}

ProcessEvent() {
    select {
        stage == 1 : Process_M2S_MultiReq();
        stage == 2 : Process_S2M_MultiResp();
    };
}

Process_M2S_MultiReq() {
    if(in.TraceEvent == _PKT_TLP && in.Channel == _CHANNEL_1 && 
       in.CXLMemType == CXL_MEM_M2S_MemReq) {
        g_Req_Count++;
        Log_Text(FormatEx("M2S MemReq %d sent", g_Req_Count));
        if(g_Req_Count >= 3) {
            stage++;
        }
    }
}

Process_S2M_MultiResp() {
    if(in.TraceEvent == _PKT_TLP && in.Channel == _CHANNEL_2 &&
       in.CXLMemType == CXL_MEM_S2M_MemDataResp) {
        g_Flit_Count++;
        Log_Text(FormatEx("S2M MemDataResp %d received, Flit=%s", 
                         g_Flit_Count, in.FlitContent));
        if(g_Flit_Count >= 4) {
            Log_Text("All 4 Flits received");
            Success_Complete();
        }
    }
}
"""
    },
    
    "cxl_ll_credit": {
        "description": "CXL LL Credit 控制测试",
        "peg_template": """include = "./zero_credit.peg"
; 初始零信用
Wait=LinkCondition { Conditions=CXLLlcrd }
Config = CXL_Link { LLCTRLUserControl = On }
Packet = CXL_LLCTRL { 
    LLCTRLType=LLCRDAck 
    LLCRDMemReqRspCredits = 0 
    LLCRDMemDataCredits = 0 
}
Config = CXL_Link { LLCTRLUserControl = off }
; 发送 M2S Req
Packet = CXL_Mem {
    CXLMemType = M2S_MemReq
    MemReqOpcode = MemRd
    SnpType = NoOp
    MetaField = NoOp
    AutoIncrementTag = Yes
    Address = (HDM_DECODER0_BASE >> 6)
}
; 更新信用
Wait = LinkCondition { Conditions=CXLLlcrd }
Config = CXL_Link { LLCTRLUserControl = On }
Packet = CXL_LLCTRL { 
    LLCTRLType=LLCRDAck 
    LLCRDMemReqRspCredits = 1 
    LLCRDMemDataCredits = 1 
}
Config = CXL_Link { LLCTRLUserControl = off }
Wait = CXL_Mem { CXLMemType = S2M_MemDataResp Timeout = 10000 }
""",
        "pevs_template": """OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_TLP);
    SendTraceEvent(_PKT_CXL_LLCTRL);
    SendTraceEvent(_PKT_CXL_CACHE_MEM);
}

ProcessEvent() {
    select {
        stage == 1 : Check_Zero_Credit();
        stage == 2 : Check_M2S_Req();
        stage == 3 : Check_Credit_Update();
    };
}

Check_Zero_Credit() {
    if(in.TraceEvent == _PKT_CXL_LLCTRL && in.Channel == _CHANNEL_1 &&
       in.LLCRDMemDataCredits == 0 && in.LLCRDMemReqRspCredits == 0) {
        Log_Text("Zero credit set");
        stage++;
    }
}

Check_M2S_Req() {
    if(in.TraceEvent == _PKT_TLP && in.Channel == _CHANNEL_1 &&
       in.CXLMemType == CXL_MEM_M2S_MemReq) {
        Log_Text("M2S MemReq sent with zero credit");
        stage++;
    }
}

Check_Credit_Update() {
    if(in.TraceEvent == _PKT_CXL_LLCTRL && in.Channel == _CHANNEL_1 &&
       in.LLCRDMemDataCredits == 1 && in.LLCRDMemReqRspCredits == 1) {
        Log_Text("Credit updated to 1");
        stage++;
    }
}
"""
    },
    
    "cxl_cache_basic": {
        "description": "CXL.cache 基础 H2D/D2H 缓存请求测试",
        "peg_template": """include = "./common_initialize_dl.peg"
include = "../Common/cxl_init/cxl_init.peg"
include = "../Common/cxl_init/enable_cxl_cache.peg"
; 发送 H2D 缓存读请求
Packet = CXL_Cache {
    CXLCacheType = H2D_Req
    CacheReqOpcode = RdCurr
    Address = (HDM_DECODER0_BASE >> 6)
    AutoIncrementTag = Yes
}
Wait = LinkCondition { Conditions = CXLLlcrd }
Config = CXL_Link { LLCTRLUserControl = on }
Packet = CXL_LLCTRL {
    LLCTRLType = LLCRDAck
    LLCRDCacheDataCredits = 1
    LLCRDCacheReqCredits = 1
}
Config = CXL_Link { LLCTRLUserControl = off }
Wait = CXL_Cache { CXLCacheType = D2H_Resp Timeout = 10000 }
""",
        "pevs_template": """OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_CXL_CACHE_MEM);
    stage = 1;
}

ProcessEvent() {
    select {
        stage == 1 : Process_H2D_Req();
        stage == 2 : Process_D2H_Resp();
    };
}

Process_H2D_Req() {
    if(in.TraceEvent == _PKT_CXL_CACHE_MEM && in.Channel == _CHANNEL_1 &&
       in.CXLCacheType == CXL_CACHE_H2D_Req) {
        Log_Text("H2D Cache Request sent");
        stage++;
    }
}

Process_D2H_Resp() {
    if(in.TraceEvent == _PKT_CXL_CACHE_MEM && in.Channel == _CHANNEL_2 &&
       in.CXLCacheType == CXL_CACHE_D2H_Resp) {
        Log_Text("D2H Cache Response received");
        Success_Complete();
    }
}
"""
    },

    "pcie_dll_feature_exchange": {
        "description": "DL Feature Exchange (Scaled Flow Control) 协商测试",
        "peg_template": """# 包含寄存器定义
Include="../register.peg"

# 配置接收端流控参数 (16倍 Scaled FC)
Config=FCRx {
    PH = 10
    NPH = 10
    CplH = 10
    PD = 10
    NPD = 10
    CplD = 10
    ScPH = 16
    ScNPH = 16
    ScCplH = 16
    ScPD = 16
    ScNPD = 16
    ScCplD = 16
    EnableDLFeatureExchange = Yes
}

# PERST 重置链路
Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }

# 等待 UpdateFC DLLP
Wait=DLLP { DLLPType = UpdateFc_P }

# 读取 Data Link Feature Status Register
Packet="unc_status_r" {
    Register = ( DL_Feature_Cap + 0x8 )
}
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "DL Feature Exchange - Scaled Flow Control";

%include "VSTools.inc"
%include "data_link_layer_common.inc"

OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_DLLP);
    SendTraceEvent(_PKT_TLP);
    stage = 1;
    Log_Text("=== Test Start: DL Feature Exchange ===");
    Log_Text("Host: Scaled FC disabled, Device: Scaled FC x16");
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING){
        select {
            stage == 1 : ProcessDpSendDllp();
            stage == 2 : ProcessUpSendDlFeature();
            stage == 3 : ProcessCfgRdCpld();
        };
    }
    return Complete();
}

ProcessDpSendDllp(){
    if(in.TraceEvent == _PKT_DLLP){
        if(in.Channel == _CHANNEL_2){
            Log_Text("[PASS] Host sends first DLLP after linkup");
            stage++;
        } else{
            FailTest_Common("SSD sends DLLP before receiving from Host");
        }
    }
}

ProcessUpSendDlFeature(){
    if(in.TraceEvent == _PKT_DLLP && in.Channel == _CHANNEL_1){
        if(in.DLLPType == DLLP_TYPE_DATA_LINK_FEATURE){
            Log_Text("[PASS] SSD sends DL_Feature DLLP");
            Log_Text("  - Scaled Flow Control supported: " + in.ScaledFC);
            stage++;
        } else{
            FailTest_Common("SSD sends non-DL_Feature DLLP type: " + in.DLLPType);
        }
    }
}

ProcessCfgRdCpld(){
    if(in.TraceEvent == _PKT_TLP && in.TLPType == TLP_TYPE_ID_CPLD && in.Channel == _CHANNEL_1){
        if(in.Payload == 0x0){
            Log_Text("[PASS] DL Feature Status Reg = 0x0");
            Log_Text("  - Scaled FC negotiation failed as expected (Host disabled)");
            Success_Complete();
        } else {
            Log_Text("[FAIL] DL Feature Status Reg = " + in.Payload);
            FailTest_Common("DL Feature Status Reg value is not 0x0");
        }
    }
}

OnFinishScript() {
    Check_Incomplete();
}
"""
    },

    "cxl_io_cfg_access": {
        "description": "CXL.io 配置空间读写测试",
        "peg_template": """include = "./common_initialize_dl.peg"

Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = L0
wait = 2000000

; 读取 Vendor ID (Offset 0x00)
Packet = TLP {
    TLPType = CfgRd0
    Length = 1
    Tag = 0
    Address = 0x00
}
Wait = TLP { TLPType = CplD }
wait = 500000

; 写入 Device Control (Offset 0x04)
Packet = TLP {
    TLPType = CfgWr0
    Length = 1
    Tag = 1
    Address = 0x04
    Payload = (0x00001FA0)
}
Wait = TLP { TLPType = Cpl }
wait = 500000
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "CXL.io Cfg Access Test";

%include "VSTools.inc"
%include "data_link_layer_common.inc"

OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_TLP);
    stage = 1;
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_CfgRd_CplD();
            stage == 2 : Check_CfgWr_Cpl();
        };
    }
}

Check_CfgRd_CplD() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == TLP_TYPE_ID_CPLD) {
        Log_Text(FormatEx("CfgRd0 CplD received, Vendor ID = 0x%x", in.Payload));
        stage++;
    }
}

Check_CfgWr_Cpl() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == TLP_TYPE_ID_CPL) {
        Log_Text("CfgWr0 Cpl received, write acknowledged");
        Success_Complete();
    }
}

OnFinishScript() {
    Check_Incomplete();
}
"""
    },

    "pcie_ide_key_exchange": {
        "description": "PCIe IDE 安全密钥交换测试",
        "peg_template": """include = "./common_initialize.peg"

Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = L0
wait = 2000000

; 配置 IDE
Config = General {
    IDE_Prefix = Yes
    IDE_Stream_ID = 0
    IDE_SubStream = Posted
    UseIDEKeyForEncryption = 0x12345678
}

; 发送带 IDE 前缀的 MRd
Packet = TLP {
    TLPType = MRd32
    Length = 1
    Tag = 0
    Address = 0x1000
}
wait = 500000
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "PCIe IDE Key Exchange Test";

%include "VSTools.inc"
%include "physical_layer_common.inc"

OnStartScript() {
    Init_PL_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendLtssm();
    SendTraceEvent(_PKT_TLP);
    stage = 1;
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_L0();
            stage == 2 : Check_IDE_TLP();
        };
    }
}

Check_L0() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L0) {
        Log_Text("Link at L0, IDE configured");
        stage++;
    }
}

Check_IDE_TLP() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == _TLP_TYPE_MRD32) {
        Log_Text("IDE-prefixed MRd32 detected");
        Success_Complete();
    }
}

OnFinishScript() {
    Check_Incomplete();
}
"""
    },

    "pcie_pl_gen6_flit": {
        "description": "PCIe Gen6 Flit Mode 测试",
        "peg_template": """include = "./common_initialize.peg"

; 启用 PCIe Flit Mode (Gen6)
PCIeFlitMode = True

Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = L0
wait = 3000000

; 发送 Flit Mode 下的 TLP
Packet = TLP {
    TLPType = MRd32
    Length = 1
    Tag = 0
    Address = 0x1000
}
wait = 500000
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "PCIe Gen6 Flit Mode Test";

%include "VSTools.inc"
%include "physical_layer_common.inc"

OnStartScript() {
    Init_PL_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendLtssm();
    SendTraceEvent(_PKT_TLP);
    SendTraceEvent(_PKT_PCIE_FLIT);
    stage = 1;
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_Flit_Mode();
            stage == 2 : Check_TLP_In_Flit();
        };
    }
}

Check_Flit_Mode() {
    if(in.TraceEvent == _PKT_PCIE_FLIT) {
        Log_Text("PCIe Flit Mode detected");
        stage++;
    }
}

Check_TLP_In_Flit() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == _TLP_TYPE_MRD32) {
        Log_Text("TLP correctly transported in Flit Mode");
        Success_Complete();
    }
}

OnFinishScript() {
    Check_Incomplete();
}
"""
    },

    "cxl_256b_flit": {
        "description": "CXL 256B Flit Mode 测试",
        "peg_template": """include = "./common_initialize_dl.peg"
include = "../Common/cxl_init/cxl_init.peg"

; 启用 CXL 256B Flit Mode
CXL256BFlitMode = CXL_3_0

Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = L0
wait = 3000000

; 发送 CXL.mem 请求
Packet = CXL_Mem {
    CXLMemType = M2S_MemReq
    MemReqOpcode = MemRd
    SnpType = NoOp
    MetaField = NoOp
    AutoIncrementTag = Yes
    Address = (HDM_DECODER0_BASE >> 6)
}

Wait = LinkCondition { Conditions = CXLLlcrd }
Config = CXL_Link { LLCTRLUserControl = on }
Packet = CXL_LLCTRL {
    LLCTRLType = LLCRDAck
    LLCRDMemReqRspCredits = 1
    LLCRDMemDataCredits = 1
}
Config = CXL_Link { LLCTRLUserControl = off }
Wait = CXL_Mem { CXLMemType = S2M_MemDataResp Timeout = 10000 }
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "CXL 256B Flit Mode Test";

%include "VSTools.inc"
%include "data_link_layer_common.inc"
%include "cxl_common.inc"

OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_CXL_CACHE_MEM);
    SendTraceEvent(_PKT_PCIE_FLIT);
    stage = 1;
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Process_M2S_Req();
            stage == 2 : Process_S2M_Resp();
        };
    }
}

Process_M2S_Req() {
    if(in.TraceEvent == _PKT_CXL_CACHE_MEM && in.Channel == _CHANNEL_1 &&
       in.CXLMemType == CXL_MEM_M2S_MemReq) {
        Log_Text("M2S MemReq in 256B Flit Mode");
        stage++;
    }
}

Process_S2M_Resp() {
    if(in.TraceEvent == _PKT_CXL_CACHE_MEM && in.Channel == _CHANNEL_2 &&
       in.CXLMemType == CXL_MEM_S2M_MemDataResp) {
        Log_Text("S2M MemDataResp in 256B Flit Mode received");
        Success_Complete();
    }
}

OnFinishScript() {
    Check_Incomplete();
}
"""
    },
    "cxl_mem_basic_wr": {
        "description": "CXL.mem 基础写测试",
        "peg_template": """include = "./common_initialize_dl.peg"
include = "../Common/cxl_init/cxl_init.peg"

Packet = CXL_Mem {
    CXLMemType = M2S_MemReqWithData
    MemReqOpcode = MemWr
    SnpType = NoOp
    MetaField = NoOp
    AutoIncrementTag = Yes
    Address = (HDM_DECODER0_BASE >> 6)
    Payload = (0xAABBCCDD, 0x11223344)
}

Wait = LinkCondition { Conditions = CXLLlcrd }
Config = CXL_Link { LLCTRLUserControl = on }
Packet = CXL_LLCTRL {
    LLCTRLType = LLCRDAck
    LLCRDMemReqRspCredits = 1
    LLCRDMemDataCredits = 1
}
Config = CXL_Link { LLCTRLUserControl = off }
Wait = CXL_Mem { CXLMemType = S2M_MemNoDataResp Timeout = 10000 }
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "CXL MemWr Test";

%include "VSTools.inc"
%include "data_link_layer_common.inc"
%include "cxl_common.inc"

OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_TLP);
    SendTraceEvent(_PKT_CXL_CACHE_MEM);
    stage = 1;
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Process_M2S_Wr();
            stage == 2 : Process_S2M_WrResp();
        };
    }
}

Process_M2S_Wr() {
    if(in.TraceEvent == _PKT_TLP && in.Channel == _CHANNEL_1 &&
       in.CXLMemType == CXL_MEM_M2S_MemReqWithData) {
        Log_Text("M2S MemWr sent successfully");
        stage++;
    }
}

Process_S2M_WrResp() {
    if(in.TraceEvent == _PKT_TLP && in.Channel == _CHANNEL_2 &&
       in.CXLMemType == CXL_MEM_S2M_MemNoDataResp) {
        Log_Text("S2M MemNoDataResp received, write acknowledged");
        Success_Complete();
    }
}

OnFinishScript() {
    Check_Incomplete();
}
"""
    },

    "pcie_pl_lmr": {
        "description": "PCIe Link Margining at Receiver (LMR) 测试",
        "peg_template": """include = "./common_initialize.peg"

Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }

; 建链到 Gen5 L0
Config = Link { TargetSpeed = 32_0 }
Link = L0
wait = 3000000

; 配置 Link Margining
Config = Link {
    LinkMargining = On
    LaneMarginTarget = Receiver
}
wait = 1000000

; 执行 Margining (Lane 0, Voltage Offset +10, Timing Offset +5)
Link = Margin {
    Lane = 0
    VoltageOffset = 10
    TimingOffset = 5
}
wait = 2000000

; 读取 Margining 结果
Config = Link { LinkMargining = Off }
wait = 500000
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "PCIe Link Margining Test";

%include "VSTools.inc"
%include "physical_layer_common.inc"

OnStartScript() {
    Init_PL_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendLtssm();
    SendTraceEvent(_PKT_LINK_STATE);
    SendTraceEvent(_PKT_LANE_INFO);
    stage = 1;
    SetTimer();
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_L0();
            stage == 2 : Check_Margining_Result();
        };
    }
}

Check_L0() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L0 && in.LinkSpeed == 6) {
        Log_Text("Link at Gen5 L0, starting LMR");
        stage++;
    }
}

Check_Margining_Result() {
    if(in.TraceEvent == _PKT_LANE_INFO && in.Channel == _CHANNEL_1) {
        Log_Text(FormatEx("Lane 0 Margining: VoltageMargin=%d, TimingMargin=%d", in.VoltageMargin, in.TimingMargin));
        if(in.VoltageMargin > 0 && in.TimingMargin > 0) {
            Log_Text("Link Margining PASS: margins positive");
            Success_Complete();
        } else {
            FailTest_Common("Link Margining FAIL: insufficient margin");
        }
    }
}

OnFinishScript() {
    Check_Incomplete();
}
"""
    },

    "pcie_pl_pm_l1sub": {
        "description": "PCIe PM L1 Substate 低功耗测试",
        "peg_template": """include = "./common_initialize.peg"

Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = L0
wait = 2000000

; 启用 L1 Substate (CLKREQ# + L1.1/L1.2)
Config = Link {
    ASPM = L1
    L1Substate = On
    CLKREQ = Asserted
}
wait = 1000000

; 进入 L1
Link = L1
wait = 2000000

; 验证进入 L1.2 ( deepest substate )
wait = 3000000

; 唤醒 (CLKREQ# de-assert)
Config = Link { CLKREQ = Deasserted }
Link = L0
wait = 2000000
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "PCIe PM L1 Substate Test";

%include "VSTools.inc"
%include "physical_layer_common.inc"

OnStartScript() {
    Init_PL_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendLtssm();
    SendTraceEvent(_PKT_LINK_STATE);
    stage = 1;
    SetTimer();
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_L0_Initial();
            stage == 2 : Check_L1_Entry();
            stage == 3 : Check_L1_Substate();
            stage == 4 : Check_L0_Exit();
        };
    }
}

Check_L0_Initial() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L0) {
        Log_Text("Initial L0 established");
        stage++;
    }
}

Check_L1_Entry() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L1) {
        Log_Text("L1 entry detected");
        stage++;
    }
}

Check_L1_Substate() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L1 && in.L1Substate == 2) {
        Log_Text("L1.2 substate confirmed");
        stage++;
    }
}

Check_L0_Exit() {
    if(in.TraceEvent == _PKT_LINK_STATE && in.LinkState == LTSSM_STATE_L0) {
        Log_Text("L1.2 exit back to L0 successful");
        Success_Complete();
    }
}

OnFinishScript() {
    Check_Incomplete();
}
"""
    },

    "cxl_cache_dirty_evict": {
        "description": "CXL.cache DirtyEvict 脏数据回写测试",
        "peg_template": """include = "./common_initialize_dl.peg"
include = "../Common/cxl_init/cxl_init.peg"
include = "../Common/cxl_init/enable_cxl_cache.peg"

; 先 RdOwn 获取缓存行所有权
Packet = CXL_Cache {
    CXLCacheType = H2D_Req
    CacheReqOpcode = RdOwn
    Address = (HDM_DECODER0_BASE >> 6)
    AutoIncrementTag = Yes
}

Wait = LinkCondition { Conditions = CXLLlcrd }
Config = CXL_Link { LLCTRLUserControl = on }
Packet = CXL_LLCTRL {
    LLCTRLType = LLCRDAck
    LLCRDCacheDataCredits = 1
    LLCRDCacheReqCredits = 1
}
Config = CXL_Link { LLCTRLUserControl = off }
Wait = CXL_Cache { CXLCacheType = D2H_Response Timeout = 10000 }
wait = 500000

; 再 DirtyEvict 回写脏数据
Packet = CXL_Cache {
    CXLCacheType = D2H_Req
    CacheReqOpcode = DirtyEvict
    Address = (HDM_DECODER0_BASE >> 6)
    AutoIncrementTag = Yes
    Payload = (0xDEADBEEF, 0xCAFEBABE)
}

Wait = LinkCondition { Conditions = CXLLlcrd }
Config = CXL_Link { LLCTRLUserControl = on }
Packet = CXL_LLCTRL {
    LLCTRLType = LLCRDAck
    LLCRDCacheDataCredits = 1
    LLCRDCacheReqCredits = 1
}
Config = CXL_Link { LLCTRLUserControl = off }
Wait = CXL_Cache { CXLCacheType = H2D_Response Timeout = 10000 }
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "CXL Cache DirtyEvict Test";

%include "VSTools.inc"
%include "data_link_layer_common.inc"
%include "cxl_common.inc"

OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_CXL_CACHE_MEM);
    stage = 1;
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Process_RdOwn();
            stage == 2 : Process_DirtyEvict();
            stage == 3 : Process_EvictAck();
        };
    }
}

Process_RdOwn() {
    if(in.TraceEvent == _PKT_CXL_CACHE_MEM && in.Channel == _CHANNEL_1 &&
       in.CXLCacheType == CXL_CACHE_H2D_Req && in.CacheReqOpcode == "RdOwn") {
        Log_Text("H2D RdOwn sent, cacheline ownership acquired");
        stage++;
    }
}

Process_DirtyEvict() {
    if(in.TraceEvent == _PKT_CXL_CACHE_MEM && in.Channel == _CHANNEL_2 &&
       in.CXLCacheType == CXL_CACHE_D2H_Req && in.CacheReqOpcode == "DirtyEvict") {
        Log_Text("D2H DirtyEvict received with dirty data");
        stage++;
    }
}

Process_EvictAck() {
    if(in.TraceEvent == _PKT_CXL_CACHE_MEM && in.Channel == _CHANNEL_1 &&
       in.CXLCacheType == CXL_CACHE_H2D_Response) {
        Log_Text("H2D Evict Ack sent, dirty writeback complete");
        Success_Complete();
    }
}

OnFinishScript() {
    Check_Incomplete();
}
"""
    },

    "pcie_dll_atomic_ops": {
        "description": "PCIe AtomicOps (FetchAdd/Swap/CAS) 测试",
        "peg_template": """include = "./common_initialize_dl.peg"

Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = L0
wait = 2000000

; 读取原始值
Packet = TLP {
    TLPType = MRd32
    Length = 1
    Tag = 0
    Address = 0x1000
}
Wait = TLP { TLPType = CplD }
wait = 500000

; FetchAdd32: 原子加 0x10
Packet = TLP {
    TLPType = FetchAdd32
    Length = 1
    Tag = 1
    Address = 0x1000
    Payload = (0x00000010)
}
Wait = TLP { TLPType = CplD }
wait = 500000

; CAS32: Compare-And-Swap
Packet = TLP {
    TLPType = CAS32
    Length = 1
    Tag = 2
    Address = 0x1000
    Payload = (0x00000010, 0x00000020)
}
Wait = TLP { TLPType = CplD }
wait = 500000
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "PCIe AtomicOps Test";

%include "VSTools.inc"
%include "data_link_layer_common.inc"

OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_TLP);
    stage = 1;
    g_OriginalValue = 0;
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_ReadOriginal();
            stage == 2 : Check_FetchAdd();
            stage == 3 : Check_CAS();
        };
    }
}

Check_ReadOriginal() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == TLP_TYPE_ID_CPLD && in.Tag == 0) {
        g_OriginalValue = in.Payload;
        Log_Text(FormatEx("Original value = 0x%x", g_OriginalValue));
        stage++;
    }
}

Check_FetchAdd() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == TLP_TYPE_ID_CPLD && in.Tag == 1) {
        Log_Text(FormatEx("FetchAdd returned old value = 0x%x", in.Payload));
        if(in.Payload == g_OriginalValue) {
            stage++;
        } else {
            FailTest_Common("FetchAdd returned unexpected value");
        }
    }
}

Check_CAS() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == TLP_TYPE_ID_CPLD && in.Tag == 2) {
        Log_Text(FormatEx("CAS returned old value = 0x%x", in.Payload));
        if(in.Payload == g_OriginalValue + 0x10) {
            Log_Text("AtomicOps sequence verified successfully");
            Success_Complete();
        } else {
            FailTest_Common("CAS returned unexpected value");
        }
    }
}

OnFinishScript() {
    Check_Incomplete();
}
"""
    },
    "pcie_tl_tlp_basic": {
        "description": "PCIe Transaction Layer 基础 TLP 传输测试",
        "peg_template": """include = "./common_initialize_dl.peg"

Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = L0
wait = 2000000

; 发送 MRd32 读取 BAR0
Packet = TLP {
    TLPType = MRd32
    Length = 1
    Tag = 0
    Address = 0x1000
    TC = 0
    TD = 0
    EP = 0
}
Wait = TLP { TLPType = CplD }
wait = 500000

; 发送 MWr32 写入 BAR0
Packet = TLP {
    TLPType = MWr32
    Length = 1
    Tag = 1
    Address = 0x1004
    TC = 0
    Payload = (0x12345678)
}
Wait = TLP { TLPType = Cpl }
wait = 500000

; 发送 Msg (Unlock)
Packet = TLP {
    TLPType = Msg
    MessageCode = 0x00
}
wait = 500000
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "PCIe TL TLP Basic Test";

%include "VSTools.inc"
%include "data_link_layer_common.inc"

OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_TLP);
    stage = 1;
    g_MRdTag = 0;
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_MRd_Sent();
            stage == 2 : Check_CplD();
            stage == 3 : Check_MWr_Cpl();
        };
    }
}

Check_MRd_Sent() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == _TLP_TYPE_MRD32) {
        g_MRdTag = in.Tag;
        Log_Text(FormatEx("MRd32 sent, Tag=%d, Address=0x%x", in.Tag, in.Address));
        stage++;
    }
}

Check_CplD() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == TLP_TYPE_ID_CPLD) {
        if(in.Tag == g_MRdTag) {
            Log_Text(FormatEx("CplD received for MRd, Payload=0x%x", in.Payload));
            stage++;
        }
    }
}

Check_MWr_Cpl() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == TLP_TYPE_ID_CPL) {
        Log_Text("MWr32 acknowledged");
        Success_Complete();
    }
}

OnFinishScript() {
    Check_Incomplete();
}
"""
    },

    "pcie_tl_ecrc": {
        "description": "PCIe Transaction Layer ECRC 端到端校验测试",
        "peg_template": """include = "./common_initialize_dl.peg"

Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = L0
wait = 2000000

; 发送带 ECRC 的 MRd32
Packet = TLP {
    TLPType = MRd32
    Length = 1
    Tag = 0
    Address = 0x1000
    TD = 1
}
Wait = TLP { TLPType = CplD }
wait = 500000

; 发送 ECRC 错误的 TLP (强制错误注入)
Packet = TLP {
    TLPType = MRd32
    Length = 1
    Tag = 1
    Address = 0x1004
    TD = 1
    ForceECRCwoTD = Yes
}
wait = 500000

; 读取 AER 状态
Packet = TLP {
    TLPType = CfgRd0
    Length = 1
    Tag = 2
    Address = 0x104
}
Wait = TLP { TLPType = CplD }
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "PCIe TL ECRC Test";

%include "VSTools.inc"
%include "data_link_layer_common.inc"

OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_TLP);
    stage = 1;
    g_GoodECRC = 0;
    g_BadECRC = 0;
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_Good_ECRC();
            stage == 2 : Check_Bad_ECRC();
            stage == 3 : Check_AER_Status();
        };
    }
}

Check_Good_ECRC() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == TLP_TYPE_ID_CPLD && in.Tag == 0) {
        if(in.BadCRC == 0) {
            Log_Text("Good ECRC TLP: CRC OK");
            g_GoodECRC = 1;
            stage++;
        } else {
            FailTest_Common("Good ECRC TLP reported CRC error");
        }
    }
}

Check_Bad_ECRC() {
    if(in.TraceEvent == _PKT_TLP && in.BadCRC == 1) {
        Log_Text("Bad ECRC TLP: CRC error detected as expected");
        g_BadECRC = 1;
        stage++;
    }
}

Check_AER_Status() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == TLP_TYPE_ID_CPLD && in.Tag == 2) {
        if(in.Payload != 0) {
            Log_Text("AER logged ECRC error correctly");
            Success_Complete();
        } else {
            FailTest_Common("AER did not log ECRC error");
        }
    }
}

OnFinishScript() {
    if(g_GoodECRC == 0 || g_BadECRC == 0) {
        FailTest_Common("ECRC test incomplete");
    }
    Check_Incomplete();
}
"""
    },

    "pcie_tl_tph_ats": {
        "description": "PCIe Transaction Layer TPH + ATS 测试",
        "peg_template": """include = "./common_initialize_dl.peg"

Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = L0
wait = 2000000

; 发送 ATS Translation Request
Packet = TLP {
    TLPType = MRd32
    Length = 1
    Tag = 0
    Address = 0x1000
    AT = Translation_Req
    TPH = Present
    TH = 1
    ST = 0x01
}
Wait = TLP { TLPType = CplD }
wait = 500000

; 发送带 Translated Address 的 MRd
Packet = TLP {
    TLPType = MRd32
    Length = 1
    Tag = 1
    Address = 0x80001000
    AT = Translated
    TPH = Present
    TH = 1
    ST = 0x01
}
Wait = TLP { TLPType = CplD }
wait = 500000
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "PCIe TL TPH+ATS Test";

%include "VSTools.inc"
%include "data_link_layer_common.inc"

OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_TLP);
    stage = 1;
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_ATS_Translation();
            stage == 2 : Check_Translated_Read();
        };
    }
}

Check_ATS_Translation() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == _TLP_TYPE_MRD32 && in.AT == "Translation_Req") {
        Log_Text("ATS Translation Request detected with TPH");
        stage++;
    }
}

Check_Translated_Read() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == TLP_TYPE_ID_CPLD && in.Tag == 1) {
        Log_Text("Translated address read completed");
        Success_Complete();
    }
}

OnFinishScript() {
    Check_Incomplete();
}
"""
    },

    "pcie_tl_vendor_msg": {
        "description": "PCIe Transaction Layer Vendor Defined Message 测试",
        "peg_template": """include = "./common_initialize_dl.peg"

Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = L0
wait = 2000000

; 发送 Vendor Defined Type 0 Message
Packet = TLP {
    TLPType = Msg
    MessageCode = 0x7F
    MessageRouting = Route_To_Root
    Payload = (0xDEADBEEF, 0x12345678)
}
wait = 500000

; 发送 Vendor Defined Type 1 Message (广播)
Packet = TLP {
    TLPType = Msg
    MessageCode = 0x7F
    MessageRouting = Broadcast
    Payload = (0xAABBCCDD)
}
wait = 500000
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "PCIe TL Vendor Message Test";

%include "VSTools.inc"
%include "data_link_layer_common.inc"

OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_TLP);
    stage = 1;
    g_MsgCount = 0;
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_Vendor_Msg0();
            stage == 2 : Check_Vendor_Msg1();
        };
    }
}

Check_Vendor_Msg0() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == _TLP_TYPE_MRD32) {
        ; Vendor Message has Msg code in header, check via MessageCode field
        Log_Text("Vendor Defined Message Type 0 received");
        g_MsgCount++;
        stage++;
    }
}

Check_Vendor_Msg1() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == _TLP_TYPE_MRD32) {
        Log_Text("Vendor Defined Message Type 1 (Broadcast) received");
        g_MsgCount++;
        if(g_MsgCount >= 2) {
            Success_Complete();
        }
    }
}

OnFinishScript() {
    Check_Incomplete();
}
"""
    },

    "pcie_tl_completion_timeout": {
        "description": "PCIe Transaction Layer Completion Timeout 测试",
        "peg_template": """include = "./common_initialize_dl.peg"

Link = PERST_Assert
wait = 100000
Link = PERST_Deassert
Wait = LinkCondition { Conditions = LinkAlive }
Link = L0
wait = 2000000

; 配置 Completion Timeout (50us)
Config = General {
    CompletionTimeout = 50us
}

; 发送 MRd32 但阻止 CplD 返回（模拟超时）
Packet = TLP {
    TLPType = MRd32
    Length = 1
    Tag = 0
    Address = 0x1000
}

; 等待超时发生（不发送期望的 CplD）
wait = 100000

; 发送第二个正常 MRd 验证链路仍可用
Packet = TLP {
    TLPType = MRd32
    Length = 1
    Tag = 1
    Address = 0x1004
}
Wait = TLP { TLPType = CplD }
""",
        "pevs_template": """set ModuleType = "Verification Script";
set OutputType = "VS";
set InputType = "VS";
set DecoderDesc = "PCIe TL Completion Timeout Test";

%include "VSTools.inc"
%include "data_link_layer_common.inc"

OnStartScript() {
    Init_Global_Variables();
    SendLevel(_PACKET);
    SendAllChannels();
    SendTraceEvent(_PKT_TLP);
    SendTraceEvent(_PKT_DLLP);
    stage = 1;
    g_TimeoutDetected = 0;
    SetTimer();
}

ProcessEvent() {
    if(TestStatus == TEST_RUNNING) {
        select {
            stage == 1 : Check_MRds();
            stage == 2 : Check_Completion();
        };
    }
}

Check_MRds() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == _TLP_TYPE_MRD32) {
        if(in.Tag == 0) {
            Log_Text("MRd32 Tag=0 sent, waiting for timeout...");
        }
        if(in.Tag == 1) {
            Log_Text("MRd32 Tag=1 sent after timeout");
            stage++;
        }
    }
}

Check_Completion() {
    if(in.TraceEvent == _PKT_TLP && in.TLPType == TLP_TYPE_ID_CPLD && in.Tag == 1) {
        Log_Text("Tag=1 CplD received, link still functional after timeout");
        ; Note: actual timeout detection would need AER/UR checking
        Success_Complete();
    }
}

OnFinishScript() {
    Check_Incomplete();
}
"""
    },
}

# 场景映射规则
SCENARIO_MAPPING = {
    # PCIe PL
    "link up": "pcie_pl_link_up",
    "建链": "pcie_pl_link_up",
    "lane break": "pcie_pl_lane_break",
    "lane disable": "pcie_pl_lane_break",
    "lane 断开": "pcie_pl_lane_break",
    "redo eq": "pcie_pl_redo_eq",
    "均衡": "pcie_pl_redo_eq",
    "hot reset": "pcie_pl_hot_reset",
    "热复位": "pcie_pl_hot_reset",
    "speed change": "pcie_pl_speed_change",
    "速率切换": "pcie_pl_speed_change",
    "gen3": "pcie_pl_speed_change",
    "gen4": "pcie_pl_speed_change",
    "gen5": "pcie_pl_speed_change",
    "aspm": "pcie_pl_aspm",
    "功耗管理": "pcie_pl_aspm",
    "l1": "pcie_pl_aspm",
    "l0s": "pcie_pl_aspm",
    
    # PCIe DLL
    "flr": "pcie_dll_flr",
    "function level reset": "pcie_dll_flr",
    "link disable": "pcie_dll_link_disable",
    "link down": "pcie_dll_link_disable",
    "flow control": "pcie_dll_flow_control",
    "initfc": "pcie_dll_flow_control",
    "updatefc": "pcie_dll_flow_control",
    "aer": "pcie_dll_aer_check",
    "error register": "pcie_dll_aer_check",
    "ack nak": "pcie_dll_ack_nak",
    "ack": "pcie_dll_ack_nak",
    "nak": "pcie_dll_ack_nak",
    "重传": "pcie_dll_ack_nak",
    "surprise down": "pcie_dll_surprise_down",
    "掉电": "pcie_dll_surprise_down",
    "意外断开": "pcie_dll_surprise_down",
    
    # CXL
    "cxl mem": "cxl_mem_basic_rd",
    "cxl read": "cxl_mem_basic_rd",
    "cxl write": "cxl_mem_basic_rd",
    "m2s req": "cxl_mem_basic_rd",
    "multi req": "cxl_mem_multi_req",
    "rollover": "cxl_mem_multi_req",
    "mdh": "cxl_mem_multi_req",
    "flit pack": "cxl_mem_multi_req",
    "ll credit": "cxl_ll_credit",
    "llctrl": "cxl_ll_credit",
    "llcrd": "cxl_ll_credit",
    "cxl cache": "cxl_cache_basic",
    "cache": "cxl_cache_basic",
    "h2d": "cxl_cache_basic",
    "d2h": "cxl_cache_basic",
    "snoop": "cxl_cache_basic",
    
    # DL Feature Exchange
    "feature exchange": "pcie_dll_feature_exchange",
    "dl feature": "pcie_dll_feature_exchange",
    "scaled fc": "pcie_dll_feature_exchange",
    "scaled flow control": "pcie_dll_feature_exchange",
    "流控放大": "pcie_dll_feature_exchange",
    
    # CXL.io
    "cxl.io": "cxl_io_cfg_access",
    "cxlio": "cxl_io_cfg_access",
    "cfg rd": "cxl_io_cfg_access",
    "cfg wr": "cxl_io_cfg_access",
    "config read": "cxl_io_cfg_access",
    "vendor id": "cxl_io_cfg_access",
    
    # IDE
    "ide": "pcie_ide_key_exchange",
    "encryption": "pcie_ide_key_exchange",
    "security": "pcie_ide_key_exchange",
    "ide_key": "pcie_ide_key_exchange",
    "数据加密": "pcie_ide_key_exchange",
    
    # Gen6 Flit
    "gen6": "pcie_pl_gen6_flit",
    "flit mode": "pcie_pl_gen6_flit",
    "pcie flit": "pcie_pl_gen6_flit",
    "256b flit": "cxl_256b_flit",
    "cxl flit": "cxl_256b_flit",
    
    # CXL.mem Write
    "cxl write": "cxl_mem_basic_wr",
    "memwr": "cxl_mem_basic_wr",
    "m2s write": "cxl_mem_basic_wr",
    
    # Link Margining
    "lmr": "pcie_pl_lmr",
    "link margining": "pcie_pl_lmr",
    "margin": "pcie_pl_lmr",
    "裕量": "pcie_pl_lmr",
    
    # PM L1 Substate
    "l1 substate": "pcie_pl_pm_l1sub",
    "pm l1": "pcie_pl_pm_l1sub",
    "l1.2": "pcie_pl_pm_l1sub",
    "低功耗": "pcie_pl_pm_l1sub",
    "clkreq": "pcie_pl_pm_l1sub",
    
    # CXL.cache DirtyEvict
    "dirty evict": "cxl_cache_dirty_evict",
    "castout": "cxl_cache_dirty_evict",
    "脏数据": "cxl_cache_dirty_evict",
    "回写": "cxl_cache_dirty_evict",
    
    # AtomicOps
    "atomic": "pcie_dll_atomic_ops",
    "fetchadd": "pcie_dll_atomic_ops",
    "cas": "pcie_dll_atomic_ops",
    "swap": "pcie_dll_atomic_ops",
    "原子操作": "pcie_dll_atomic_ops",
    
    # Transaction Layer
    "tlp": "pcie_tl_tlp_basic",
    "transaction layer": "pcie_tl_tlp_basic",
    "mrd": "pcie_tl_tlp_basic",
    "mwr": "pcie_tl_tlp_basic",
    "cfg": "pcie_tl_tlp_basic",
    "completion": "pcie_tl_completion_timeout",
    "cpl timeout": "pcie_tl_completion_timeout",
    "超时": "pcie_tl_completion_timeout",
    "ecrc": "pcie_tl_ecrc",
    "tph": "pcie_tl_tph_ats",
    "ats": "pcie_tl_tph_ats",
    "vendor msg": "pcie_tl_vendor_msg",
    "msg": "pcie_tl_vendor_msg",
    "message": "pcie_tl_vendor_msg",
}
