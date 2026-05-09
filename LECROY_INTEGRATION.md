# LeCroy Script Agent 集成文档

## 集成完成的功能

### 后端 API

1. **生成单个脚本**
```
POST /api/projects/{project_id}/generate-lecroy-script
```
请求体:
```json
{
  "case_id": 123,
  "case_content": "测试描述",
  "case_name": "Test_Name"
}
```

2. **批量生成脚本**
```
POST /api/projects/{project_id}/generate-lecroy-scripts-batch
```

3. **获取脚本列表**
```
GET /api/projects/{project_id}/lecroy-scripts
```

4. **获取单个脚本内容**
```
GET /api/projects/{project_id}/lecroy-scripts/{script_name}
```

### 前端功能

1. **新增 "LeCroy脚本" Tab**
   - 位于测试用例 Tab 右侧
   - 显示所有生成的脚本列表

2. **操作按钮**
   - "生成脚本": 为当前项目的测试用例生成 LeCroy 脚本
   - "批量生成": 批量生成所有测试用例的脚本

3. **脚本查看**
   - 点击"查看"按钮打开 Modal
   - 显示 PEG 和 PEVS 脚本内容
   - 支持复制脚本内容

### 生成的文件结构

```
storage-test-ai/
├── lecroy_scripts/
│   └── project_{id}/
│       ├── Test_Name_20250710_164533.peg
│       ├── Test_Name_20250710_164533.pevs
│       └── ...
```

## 支持的测试场景

| 协议层 | 场景 |
|--------|------|
| PCIe PL | Link Up, Lane Break, RedoEQ, Hot Reset |
| PCIe DLL | FLR, Link Disable, Flow Control, AER |
| CXL LL | MemRd, MemWr, Flit Pack, MDH, LL Credit |

## 使用方法

1. **创建项目并生成测试用例**
   - 在平台上完成策略 → 设计 → 用例的生成流程

2. **生成 LeCroy 脚本**
   - 进入项目详情页
   - 切换到 "LeCroy脚本" Tab
   - 点击 "生成脚本" 或 "批量生成"

3. **查看和使用脚本**
   - 点击脚本名称旁的"查看"按钮
   - 复制 PEG/PEVS 内容到 LeCroy 软件

## 后续扩展

1. **直接下发执行** - 通过 LeCroy API 远程执行脚本
2. **结果回传** - 将执行结果和 Trace 文件关联到测试用例
3. **更多协议** - 支持 CXL.cache, CXL.io

## 文件变更

### 新增文件
- `backend/services/lecrory_integration.py` - 后端集成服务
- `frontend/src/services/lecroryApi.ts` - 前端 API 客户端
- `lecroy_script_agent/` - 独立的脚本生成 Agent

### 修改文件
- `backend/main.py` - 添加 API 端点
- `frontend/src/pages/ProjectDetail.tsx` - 添加 UI

