import { FC, useEffect, useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import {
  Play, FileText, CheckCircle, Clock, Square, Settings2, X, Edit2, Copy, Trash2, Save,
  FileCode, Terminal, Upload, RefreshCw, ShieldCheck, BookOpen, TestTube,
  ClipboardCopy, Loader2, AlertCircle, Layers, Zap, ChevronRight
} from 'lucide-react'
import axios from 'axios'
import { lecroyApi, LeCroyScriptInfo } from '../services/lecroryApi'

interface Project {
  id: number
  name: string
  device_type: string
  requirements: string
  status: string
}

interface Deliverable {
  id: number
  type: string
  status: string
  content: string
}

interface WorkflowStatus {
  status: string
  current_stage: string | null
  progress: number
  message: string | null
  task_id?: string
  can_stop: boolean
}

interface Template {
  id: number
  name: string
  description: string | null
  type: 'strategy' | 'design' | 'case'
  content: string
  is_default: boolean
  is_editable: boolean
  parent_id: number | null
  created_by: string
  created_at: string
  updated_at: string
}

const copyToClipboard = async (text: string) => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.left = '-9999px'
      document.body.appendChild(textarea)
      textarea.focus()
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    alert('已复制到剪贴板')
  } catch {
    alert('复制失败，请手动复制')
  }
}

const downloadFile = (content: string, filename: string) => {
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const ProjectDetail: FC = () => {
  const { id } = useParams<{ id: string }>()
  const [project, setProject] = useState<Project | null>(null)
  const [deliverables, setDeliverables] = useState<Deliverable[]>([])
  const [workflow, setWorkflow] = useState<WorkflowStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  // 模板相关状态
  const [templates, setTemplates] = useState<Template[]>([])
  const [showTemplateSelector, setShowTemplateSelector] = useState<'strategy' | 'design' | 'cases' | null>(null)
  const [showTemplateEditor, setShowTemplateEditor] = useState(false)
  const [showTemplateManager, setShowTemplateManager] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null)
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null)
  const [useTemplate, setUseTemplate] = useState(true)

  // LeCroy Script 相关状态
  const [lecroyScripts, setLecroyScripts] = useState<LeCroyScriptInfo[]>([])
  const [selectedScript, setSelectedScript] = useState<{
    id: number;
    test_name: string;
    protocol: string | null;
    scenario: string | null;
    description: string | null;
    peg_content: string;
    pevs_content: string;
    generation_mode: string | null;
    feedback_history: Array<{ feedback: string; timestamp: string; reasoning: string }>;
    optimized_from: number | null;
  } | null>(null)
  const [generatingScript, setGeneratingScript] = useState(false)
  const [showScriptModal, setShowScriptModal] = useState(false)
  const [lecroyDescription, setLecroyDescription] = useState('')
  const [lecroyTestName, setLecroyTestName] = useState('')
  const [generationMode, setGenerationMode] = useState<'template' | 'llm' | 'hybrid'>('hybrid')
  const [optimizeFeedback, setOptimizeFeedback] = useState('')
  const [optimizing, setOptimizing] = useState(false)
  const [pegPage, setPegPage] = useState(1)
  const [pevsPage, setPevsPage] = useState(1)
  const [scriptListPage, setScriptListPage] = useState(1)
  const SCRIPT_LINES_PER_PAGE = 50
  const SCRIPTS_PER_PAGE = 10

  // PRD 上传相关状态
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetchData()
    fetchTemplates()
    if (activeTab === 'lecroy') {
      fetchLecroyScripts()
    }
    const interval = setInterval(fetchData, 2000)
    return () => clearInterval(interval)
  }, [id, activeTab])

  const fetchData = async () => {
    try {
      const [projectRes, deliverablesRes, workflowRes] = await Promise.all([
        axios.get(`/api/projects/${id}`),
        axios.get(`/api/projects/${id}/deliverables`),
        axios.get(`/api/workflow/status/${id}`),
      ])
      setProject(projectRes.data)
      setDeliverables(deliverablesRes.data)
      setWorkflow(workflowRes.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchTemplates = async () => {
    try {
      const res = await axios.get('/api/templates')
      setTemplates(res.data)
    } catch (err) {
      console.error('Failed to fetch templates:', err)
    }
  }

  // LeCroy Script 相关函数
  const fetchLecroyScripts = async () => {
    if (!id) return
    try {
      const data = await lecroyApi.getScripts(id)
      setLecroyScripts(data.scripts)
    } catch (err) {
      console.error('Failed to fetch LeCroy scripts:', err)
    }
  }

  const generateLecroyScript = async () => {
    if (!lecroyDescription.trim()) {
      alert('请输入测试步骤描述')
      return
    }

    setGeneratingScript(true)
    try {
      const result = await lecroyApi.generateScript(id!, {
        description: lecroyDescription.trim(),
        test_name: lecroyTestName.trim() || undefined,
        mode: generationMode
      })

      if (result.success) {
        alert(`脚本生成成功: ${result.test_name} (${result.generation_mode})`)
        setLecroyDescription('')
        setLecroyTestName('')
        setScriptListPage(1)
        fetchLecroyScripts()
      } else {
        alert(`生成失败: ${result.error}`)
      }
    } catch (err: any) {
      alert(`生成错误: ${err.message}`)
    } finally {
      setGeneratingScript(false)
    }
  }

  const optimizeScript = async () => {
    if (!selectedScript) return
    if (!optimizeFeedback.trim()) {
      alert('请输入优化建议')
      return
    }

    setOptimizing(true)
    try {
      const result = await lecroyApi.optimizeScript(id!, {
        script_id: selectedScript.id,
        feedback: optimizeFeedback.trim()
      })

      if (result.success) {
        alert(`优化成功: ${result.test_name}`)
        setOptimizeFeedback('')
        // 刷新当前脚本详情
        const updated = await lecroyApi.getScript(id!, result.id!)
        setSelectedScript(updated)
        fetchLecroyScripts()
      } else {
        alert(`优化失败: ${result.error}`)
      }
    } catch (err: any) {
      alert(`优化错误: ${err.message}`)
    } finally {
      setOptimizing(false)
    }
  }

  const viewScript = async (scriptId: number) => {
    try {
      const script = await lecroyApi.getScript(id!, scriptId)
      setSelectedScript(script)
      setShowScriptModal(true)
      setOptimizeFeedback('')
      setPegPage(1)
      setPevsPage(1)
    } catch (err: any) {
      alert(`加载脚本失败: ${err.message}`)
    }
  }

  const deleteScript = async (scriptId: number) => {
    if (!confirm('确定要删除此脚本吗？')) return
    try {
      await lecroyApi.deleteScript(id!, scriptId)
      setScriptListPage(1)
      fetchLecroyScripts()
    } catch (err: any) {
      alert(`删除失败: ${err.message}`)
    }
  }

  const generateStrategy = async () => {
    setShowTemplateSelector('strategy')
    const strategyTemplates = templates.filter(t => t.type === 'strategy')
    if (strategyTemplates.length > 0 && !selectedTemplateId) {
      setSelectedTemplateId(strategyTemplates[0].id)
    }
  }

  const generateDesign = async () => {
    const strategy = deliverables.find(d => d.type === 'strategy')
    if (!strategy || strategy.status !== 'completed') {
      alert('请先生成测试策略')
      return
    }
    setShowTemplateSelector('design')
    const designTemplates = templates.filter(t => t.type === 'design')
    if (designTemplates.length > 0 && !selectedTemplateId) {
      setSelectedTemplateId(designTemplates[0].id)
    }
  }

  const generateCases = async () => {
    const design = deliverables.find(d => d.type === 'design')
    if (!design || design.status !== 'completed') {
      alert('请先生成测试设计')
      return
    }
    setShowTemplateSelector('cases')
    const caseTemplates = templates.filter(t => t.type === 'case')
    if (caseTemplates.length > 0 && !selectedTemplateId) {
      setSelectedTemplateId(caseTemplates[0].id)
    }
  }

  const confirmGenerate = async (stage: 'strategy' | 'design' | 'cases') => {
    try {
      const endpoint = stage === 'strategy' ? 'generate-strategy' :
        stage === 'design' ? 'generate-design' : 'generate-cases'

      await axios.post(`/api/projects/${id}/${endpoint}`, {
        template: selectedTemplateId ? String(selectedTemplateId) : null,
        use_template: useTemplate
      })

      setShowTemplateSelector(null)
      setSelectedTemplateId(null)
      fetchData()
    } catch (err: any) {
      console.error(err)
      alert(err.response?.data?.detail || '生成失败，请重试')
    }
  }

  const stopTask = async () => {
    if (!workflow?.can_stop) {
      alert('当前没有可终止的运行中任务')
      return
    }
    if (!confirm('确定要终止当前任务吗？')) return

    try {
      await axios.post(`/api/workflow/stop/${id}`)
      // 立即更新本地状态，给用户即时反馈
      setWorkflow(prev => prev ? { ...prev, status: 'cancelled', can_stop: false, message: '正在终止...' } : null)
      fetchData()
    } catch (err: any) {
      console.error(err)
      alert(err.response?.data?.detail || '终止任务失败')
    }
  }

  // 模板管理功能
  const openTemplateEditor = (template: Template) => {
    if (template.is_default && !template.is_editable) {
      cloneTemplate(template.id)
      return
    }
    setEditingTemplate({ ...template })
    setShowTemplateEditor(true)
  }

  const saveTemplate = async () => {
    if (!editingTemplate) return

    try {
      await axios.put(`/api/templates/${editingTemplate.id}`, {
        name: editingTemplate.name,
        description: editingTemplate.description,
        content: editingTemplate.content
      })
      setShowTemplateEditor(false)
      setEditingTemplate(null)
      fetchTemplates()
    } catch (err) {
      console.error(err)
      alert('保存模板失败')
    }
  }

  const cloneTemplate = async (templateId: number) => {
    try {
      const res = await axios.post(`/api/templates/${templateId}/clone`)
      fetchTemplates()
      setEditingTemplate(res.data)
      setShowTemplateEditor(true)
    } catch (err) {
      console.error(err)
      alert('克隆模板失败')
    }
  }

  const deleteTemplate = async (templateId: number) => {
    if (!confirm('确定要删除此模板吗？')) return

    try {
      await axios.delete(`/api/templates/${templateId}`)
      fetchTemplates()
    } catch (err) {
      console.error(err)
      alert('删除模板失败')
    }
  }

  const createNewTemplate = async (type: 'strategy' | 'design' | 'case') => {
    const name = prompt('请输入模板名称:')
    if (!name) return

    try {
      const res = await axios.post('/api/templates', {
        name,
        type,
        content: `# ${name}\n\n请在此处编辑模板内容...`,
        description: '用户自定义模板'
      })
      fetchTemplates()
      setEditingTemplate(res.data)
      setShowTemplateEditor(true)
    } catch (err) {
      console.error(err)
      alert('创建模板失败')
    }
  }

  // PRD 上传功能
  const handleFileSelect = async (file: File) => {
    const validExts = ['.txt', '.md', '.docx']
    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
    if (!validExts.includes(ext)) {
      alert('不支持的文件类型，请上传 .txt, .md 或 .docx 文件')
      return
    }
    const formData = new FormData()
    formData.append('file', file)
    setUploading(true)
    try {
      await axios.post(`/api/projects/${id}/upload-prd`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      await fetchData()
    } catch (err: any) {
      alert(err.response?.data?.detail || '上传失败，请重试')
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleFileSelect(file)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  if (loading || !project) {
    return (
      <div className="flex items-center justify-center h-64 animate-[fadeIn_0.3s_ease-out]">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    )
  }

  const strategy = deliverables.find(d => d.type === 'strategy')
  const design = deliverables.find(d => d.type === 'design')
  const cases = deliverables.find(d => d.type === 'case')

  const isRunning = workflow?.status === 'running'

  const getTemplatesForStage = () => {
    if (!showTemplateSelector) return []
    const typeMap: Record<string, string> = {
      'strategy': 'strategy',
      'design': 'design',
      'cases': 'case'
    }
    return templates.filter(t => t.type === typeMap[showTemplateSelector])
  }

  // 中文状态映射
  const stageLabels: Record<string, string> = {
    'strategy': '测试策略',
    'design': '测试设计',
    'cases': '测试用例',
  }
  const statusLabels: Record<string, string> = {
    'completed': '已完成',
    'running': '运行中',
    'idle': '空闲',
    'failed': '失败',
    'cancelled': '已终止',
    'created': '已创建',
    'strategy_generating': '生成策略中',
    'design_generating': '生成设计中',
    'cases_generating': '生成用例中',
  }
  const getStageLabel = (stage: string | null | undefined) => stage ? (stageLabels[stage] || stage) : ''
  const getStatusLabel = (status: string | null | undefined) => status ? (statusLabels[status] || status) : ''

  const renderContentBlock = (content: string) => (
    <div className="relative group animate-[fadeIn_0.4s_ease-out]">
      <button
        onClick={() => copyToClipboard(content)}
        className="absolute top-3 right-3 z-10 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-700/80 text-slate-300 text-xs opacity-0 group-hover:opacity-100 transition-all hover:bg-slate-600 hover:text-white backdrop-blur-sm"
      >
        <ClipboardCopy className="w-3.5 h-3.5" />
        复制
      </button>
      <pre className="whitespace-pre-wrap font-mono text-sm bg-slate-900 text-slate-100 p-6 rounded-xl overflow-x-auto leading-relaxed">
        {content}
      </pre>
    </div>
  )

  const tabs = [
    { id: 'overview', label: '概览', icon: <Layers className="w-4 h-4" /> },
    { id: 'strategy', label: '测试策略', icon: <ShieldCheck className="w-4 h-4" /> },
    { id: 'design', label: '测试设计', icon: <BookOpen className="w-4 h-4" /> },
    { id: 'cases', label: '测试用例', icon: <TestTube className="w-4 h-4" /> },
    { id: 'lecroy', label: 'LeCroy脚本', icon: <Terminal className="w-4 h-4" /> },
  ]

  return (
    <div className="space-y-6 animate-[fadeIn_0.5s_ease-out]">
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        @keyframes indeterminate {
          0% { transform: translateX(-100%); }
          50% { transform: translateX(0%); }
          100% { transform: translateX(100%); }
        }
      `}</style>

      {/* 项目头部 */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800 via-indigo-900 to-slate-900 p-8 text-white shadow-xl animate-[slideUp_0.4s_ease-out]">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full -translate-y-1/2 translate-x-1/3 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-500/10 rounded-full translate-y-1/2 -translate-x-1/3 blur-3xl" />
        <div className="relative z-10 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2">{project.name}</h1>
            <div className="flex items-center gap-3 text-slate-300">
              <span className="flex items-center gap-1.5 text-sm">
                <Layers className="w-4 h-4" />
                {project.device_type}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowTemplateManager(true)}
              className="flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-xl text-sm font-medium hover:bg-white/20 transition-colors border border-white/10"
            >
              <Settings2 className="w-4 h-4" />
              模板管理
            </button>
            <span className={`
              inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold backdrop-blur-sm border
              ${project.status === 'completed'
                ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25'
                : 'bg-blue-500/15 text-blue-300 border-blue-500/25'
              }
            `}>
              {project.status === 'completed' ? <CheckCircle className="w-3.5 h-3.5" /> : <Clock className="w-3.5 h-3.5" />}
              {getStatusLabel(project.status)}
            </span>
          </div>
        </div>
      </div>

      {/* 需求文档区域 */}
      <div className="animate-[slideUp_0.45s_ease-out]">
        {/* 隐藏的 file input，始终存在以确保重新上传可用 */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.md,.docx"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFileSelect(file)
            e.target.value = ''
          }}
        />
        {project.requirements ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-blue-50 rounded-lg">
                  <FileText className="w-5 h-5 text-blue-600" />
                </div>
                <h3 className="font-semibold text-slate-800">需求文档</h3>
              </div>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-blue-700 bg-blue-50 rounded-xl hover:bg-blue-100 transition-colors disabled:opacity-50"
              >
                {uploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                重新上传
              </button>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
              <p className="text-sm text-slate-700 leading-relaxed font-mono">
                {project.requirements.slice(0, 500)}
                {project.requirements.length > 500 && (
                  <span className="text-slate-400"> ...</span>
                )}
              </p>
            </div>
          </div>
        ) : (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`
              relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300
              ${isDragging
                ? 'border-blue-400 bg-blue-50/60 shadow-lg scale-[1.01]'
                : 'border-slate-300 bg-slate-50/60 hover:border-slate-400 hover:bg-slate-50 hover:shadow-md'
              }
            `}
          >
            {uploading ? (
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
                <p className="text-sm font-medium text-slate-700">正在上传...</p>
              </div>
            ) : (
              <>
                <div className={`
                  w-14 h-14 mx-auto mb-4 rounded-2xl flex items-center justify-center transition-colors
                  ${isDragging ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-400'}
                `}>
                  <Upload className="w-7 h-7" />
                </div>
                <p className="text-sm font-medium text-slate-700">点击或拖拽上传需求文档</p>
                <p className="text-xs text-slate-500 mt-1.5">支持 .txt, .md, .docx</p>
              </>
            )}
          </div>
        )}
      </div>

      {/* 运行中状态 */}
      {isRunning && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl p-5 shadow-sm animate-[slideUp_0.3s_ease-out]">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-xl">
                <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
              </div>
              <div>
                <p className="font-semibold text-slate-800">正在生成 {getStageLabel(workflow?.current_stage)}</p>
                <p className="text-xs text-slate-500 mt-0.5">{workflow?.message || '请稍候...'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-blue-600 tabular-nums">{workflow?.progress || 0}%</span>
              <button
                onClick={stopTask}
                className="flex items-center gap-1.5 px-4 py-2 bg-red-50 text-red-600 rounded-xl text-sm font-medium hover:bg-red-100 transition-colors border border-red-100"
              >
                <Square className="w-4 h-4 fill-current" />
                终止任务
              </button>
            </div>
          </div>
          <div className="w-full bg-blue-100 rounded-full h-2.5 overflow-hidden relative">
            {/* 进度条主体 */}
            <div
              className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full rounded-full transition-all duration-500 ease-out relative"
              style={{ width: `${workflow?.progress || 0}%` }}
            >
              {/* 进度条光泽动画 */}
              <div className="absolute inset-0 bg-white/20 rounded-full animate-[shimmer_1.5s_infinite]" />
            </div>
            {/* 当进度为0时显示 indeterminate 动画 */}
            {(workflow?.progress || 0) === 0 && (
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-300/40 to-transparent animate-[indeterminate_1.5s_infinite]" />
            )}
          </div>
        </div>
      )}

      {/* 三个阶段卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 animate-[slideUp_0.5s_ease-out]">
        {/* 测试策略 */}
        <div className={`
          relative group rounded-2xl p-5 border transition-all duration-300
          ${strategy?.status === 'completed'
            ? 'bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200 shadow-md'
            : 'bg-white border-slate-200 hover:shadow-lg hover:-translate-y-0.5'
          }
        `}>
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`
                p-2.5 rounded-xl transition-colors
                ${strategy?.status === 'completed' ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-500'}
              `}>
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-800">测试策略</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {strategy?.status === 'completed' ? '已完成' : '待生成'}
                </p>
              </div>
            </div>
            {strategy?.status === 'completed' && (
              <div className="flex items-center justify-center w-7 h-7 rounded-full bg-emerald-100 text-emerald-600">
                <CheckCircle className="w-4 h-4" />
              </div>
            )}
          </div>
          <button
            onClick={generateStrategy}
            disabled={isRunning}
            className={`
              w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium transition-all
              ${isRunning
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm hover:shadow-md'
              }
            `}
          >
            <Play className="w-4 h-4" />
            {strategy ? '重新生成' : '生成策略'}
          </button>
        </div>

        {/* 测试设计 */}
        <div className={`
          relative group rounded-2xl p-5 border transition-all duration-300
          ${design?.status === 'completed'
            ? 'bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200 shadow-md'
            : 'bg-white border-slate-200 hover:shadow-lg hover:-translate-y-0.5'
          }
          ${(!strategy || strategy.status !== 'completed') ? 'opacity-75' : ''}
        `}>
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`
                p-2.5 rounded-xl transition-colors
                ${design?.status === 'completed' ? 'bg-amber-100 text-amber-600' : 'bg-slate-100 text-slate-500'}
              `}>
                <BookOpen className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-800">测试设计</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {design?.status === 'completed' ? '已完成' : strategy?.status === 'completed' ? '可生成' : '需先完成策略'}
                </p>
              </div>
            </div>
            {design?.status === 'completed' && (
              <div className="flex items-center justify-center w-7 h-7 rounded-full bg-emerald-100 text-emerald-600">
                <CheckCircle className="w-4 h-4" />
              </div>
            )}
          </div>
          {(!strategy || strategy.status !== 'completed') && (
            <div className="flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 px-3 py-2 rounded-lg mb-3 border border-amber-100">
              <AlertCircle className="w-3.5 h-3.5" />
              需先完成测试策略
            </div>
          )}
          <button
            onClick={generateDesign}
            disabled={!strategy || strategy.status !== 'completed' || isRunning}
            className={`
              w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium transition-all
              ${(!strategy || strategy.status !== 'completed' || isRunning)
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-amber-500 text-white hover:bg-amber-600 shadow-sm hover:shadow-md'
              }
            `}
          >
            <Play className="w-4 h-4" />
            {design ? '重新生成' : '生成设计'}
          </button>
        </div>

        {/* 测试用例 */}
        <div className={`
          relative group rounded-2xl p-5 border transition-all duration-300
          ${cases?.status === 'completed'
            ? 'bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200 shadow-md'
            : 'bg-white border-slate-200 hover:shadow-lg hover:-translate-y-0.5'
          }
          ${(!design || design.status !== 'completed') ? 'opacity-75' : ''}
        `}>
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`
                p-2.5 rounded-xl transition-colors
                ${cases?.status === 'completed' ? 'bg-purple-100 text-purple-600' : 'bg-slate-100 text-slate-500'}
              `}>
                <TestTube className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-800">测试用例</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {cases?.status === 'completed' ? '已完成' : design?.status === 'completed' ? '可生成' : '需先完成设计'}
                </p>
              </div>
            </div>
            {cases?.status === 'completed' && (
              <div className="flex items-center justify-center w-7 h-7 rounded-full bg-emerald-100 text-emerald-600">
                <CheckCircle className="w-4 h-4" />
              </div>
            )}
          </div>
          {(!design || design.status !== 'completed') && (
            <div className="flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 px-3 py-2 rounded-lg mb-3 border border-amber-100">
              <AlertCircle className="w-3.5 h-3.5" />
              需先完成测试设计
            </div>
          )}
          <button
            onClick={generateCases}
            disabled={!design || design.status !== 'completed' || isRunning}
            className={`
              w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium transition-all
              ${(!design || design.status !== 'completed' || isRunning)
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-purple-600 text-white hover:bg-purple-700 shadow-sm hover:shadow-md'
              }
            `}
          >
            <Play className="w-4 h-4" />
            {cases ? '重新生成' : '生成用例'}
          </button>
        </div>
      </div>

      {/* 模板选择弹窗 */}
      {showTemplateSelector && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-50 animate-[fadeIn_0.2s_ease-out]">
          <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl w-[600px] max-w-[calc(100vw-2rem)] max-h-[80vh] overflow-hidden flex flex-col animate-[slideUp_0.3s_ease-out]">
            <div className="flex justify-between items-center p-6 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-800">
                {showTemplateSelector === 'strategy' && '选择测试策略模板'}
                {showTemplateSelector === 'design' && '选择测试设计模板'}
                {showTemplateSelector === 'cases' && '选择测试用例模板'}
              </h3>
              <button onClick={() => setShowTemplateSelector(null)} className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto flex-1">
              <div className="mb-4 p-3 bg-slate-50 rounded-xl border border-slate-100">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useTemplate}
                    onChange={(e) => setUseTemplate(e.target.checked)}
                    className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-slate-700">使用模板生成（推荐，输出更规范）</span>
                </label>
              </div>

              {useTemplate && (
                <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
                  {getTemplatesForStage().map(template => (
                    <label
                      key={template.id}
                      className={`
                        flex items-start gap-3 p-4 border rounded-xl cursor-pointer transition-all
                        ${selectedTemplateId === template.id
                          ? 'border-blue-300 bg-blue-50/50 shadow-sm'
                          : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                        }
                      `}
                    >
                      <input
                        type="radio"
                        name="template"
                        checked={selectedTemplateId === template.id}
                        onChange={() => setSelectedTemplateId(template.id)}
                        className="mt-1 w-4 h-4 text-blue-600 border-slate-300 focus:ring-blue-500"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-slate-800">{template.name}</span>
                          {template.is_default && (
                            <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full border border-blue-100">默认</span>
                          )}
                        </div>
                        <div className="text-sm text-slate-500 mt-1">{template.description}</div>
                        <div className="flex gap-3 mt-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              openTemplateEditor(template)
                            }}
                            className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                          >
                            查看/编辑
                          </button>
                          {template.is_default && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                cloneTemplate(template.id)
                              }}
                              className="text-xs text-emerald-600 hover:text-emerald-800 font-medium"
                            >
                              创建副本
                            </button>
                          )}
                        </div>
                      </div>
                    </label>
                  ))}

                  {getTemplatesForStage().length === 0 && (
                    <div className="text-center py-8 text-slate-500">
                      暂无模板，请先在模板管理中创建
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex gap-3 p-6 border-t border-slate-100 bg-slate-50/50">
              <button
                onClick={() => setShowTemplateSelector(null)}
                className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-slate-700 font-medium hover:bg-white hover:border-slate-300 transition-all"
              >
                取消
              </button>
              <button
                onClick={() => confirmGenerate(showTemplateSelector)}
                disabled={useTemplate && !selectedTemplateId}
                className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
              >
                开始生成
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 模板编辑器 */}
      {showTemplateEditor && editingTemplate && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-50 animate-[fadeIn_0.2s_ease-out]">
          <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl w-[900px] max-w-[95vw] h-[85vh] flex flex-col animate-[slideUp_0.3s_ease-out] overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-800">编辑模板</h3>
              <button onClick={() => setShowTemplateEditor(false)} className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">模板名称</label>
                <input
                  type="text"
                  value={editingTemplate.name}
                  onChange={(e) => setEditingTemplate({ ...editingTemplate, name: e.target.value })}
                  className="w-full px-3.5 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">描述</label>
                <input
                  type="text"
                  value={editingTemplate.description || ''}
                  onChange={(e) => setEditingTemplate({ ...editingTemplate, description: e.target.value })}
                  className="w-full px-3.5 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
                />
              </div>
              <div className="flex-1 flex flex-col min-h-[300px]">
                <label className="block text-sm font-medium text-slate-700 mb-1.5">模板内容 (Markdown)</label>
                <textarea
                  value={editingTemplate.content}
                  onChange={(e) => setEditingTemplate({ ...editingTemplate, content: e.target.value })}
                  className="flex-1 w-full px-3.5 py-2.5 border border-slate-200 rounded-xl font-mono text-sm resize-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all bg-slate-50"
                  placeholder="在此编辑模板内容..."
                />
              </div>
            </div>

            <div className="flex gap-3 p-6 border-t border-slate-100 bg-slate-50/50">
              <button
                onClick={() => setShowTemplateEditor(false)}
                className="px-5 py-2.5 border border-slate-200 rounded-xl text-slate-700 font-medium hover:bg-white hover:border-slate-300 transition-all"
              >
                取消
              </button>
              <button
                onClick={saveTemplate}
                className="flex items-center gap-1.5 px-5 py-2.5 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700 transition-all shadow-sm"
              >
                <Save className="w-4 h-4" />
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 模板管理器 */}
      {showTemplateManager && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-50 animate-[fadeIn_0.2s_ease-out]">
          <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl w-[900px] max-w-[95vw] h-[85vh] flex flex-col animate-[slideUp_0.3s_ease-out] overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-800">模板管理</h3>
              <button onClick={() => setShowTemplateManager(false)} className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 border-b border-slate-100 bg-slate-50/50">
              <div className="flex gap-2">
                <button
                  onClick={() => createNewTemplate('strategy')}
                  className="px-4 py-2 bg-blue-50 text-blue-700 rounded-xl hover:bg-blue-100 text-sm font-medium transition-colors border border-blue-100"
                >
                  + 新建策略模板
                </button>
                <button
                  onClick={() => createNewTemplate('design')}
                  className="px-4 py-2 bg-amber-50 text-amber-700 rounded-xl hover:bg-amber-100 text-sm font-medium transition-colors border border-amber-100"
                >
                  + 新建设计模板
                </button>
                <button
                  onClick={() => createNewTemplate('case')}
                  className="px-4 py-2 bg-purple-50 text-purple-700 rounded-xl hover:bg-purple-100 text-sm font-medium transition-colors border border-purple-100"
                >
                  + 新建用例模板
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {(['strategy', 'design', 'case'] as const).map(type => {
                const typeTemplates = templates.filter(t => t.type === type)
                const typeNames = { strategy: '测试策略', design: '测试设计', case: '测试用例' }
                return (
                  <div key={type} className="mb-8 last:mb-0">
                    <h4 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                      {typeNames[type]}模板
                    </h4>
                    <div className="space-y-2">
                      {typeTemplates.map(template => (
                        <div
                          key={template.id}
                          className="flex items-center justify-between p-4 bg-white border border-slate-200 rounded-xl hover:shadow-sm hover:border-slate-300 transition-all"
                        >
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-slate-800">{template.name}</span>
                              {template.is_default && (
                                <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full border border-blue-100">默认</span>
                              )}
                              {!template.is_default && (
                                <span className="text-xs bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded-full border border-emerald-100">自定义</span>
                              )}
                            </div>
                            <div className="text-sm text-slate-500 mt-0.5">{template.description}</div>
                          </div>
                          <div className="flex gap-1 ml-3">
                            <button
                              onClick={() => openTemplateEditor(template)}
                              className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                              title="编辑"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            {template.is_default && (
                              <button
                                onClick={() => cloneTemplate(template.id)}
                                className="p-2 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                                title="克隆"
                              >
                                <Copy className="w-4 h-4" />
                              </button>
                            )}
                            {!template.is_default && (
                              <button
                                onClick={() => deleteTemplate(template.id)}
                                className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                title="删除"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </div>
                      ))}

                      {typeTemplates.length === 0 && (
                        <div className="text-center py-4 text-slate-400 text-sm bg-slate-50 rounded-xl border border-dashed border-slate-200">
                          暂无{typeNames[type]}模板
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* 内容展示区域 */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden animate-[slideUp_0.55s_ease-out]">
        {/* Tab 导航 */}
        <div className="flex items-center gap-1 p-2 bg-slate-50/80 border-b border-slate-100">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200
                ${activeTab === tab.id
                  ? 'bg-white text-blue-700 shadow-sm border border-slate-200/60'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                }
              `}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-5 animate-[fadeIn_0.3s_ease-out]">
              <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" />
                生成状态概览
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className={`
                  p-4 rounded-xl border transition-all
                  ${strategy?.status === 'completed'
                    ? 'bg-emerald-50 border-emerald-200'
                    : 'bg-slate-50 border-slate-200'
                  }
                `}>
                  <div className="text-sm text-slate-500 mb-1">测试策略</div>
                  <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                    {strategy?.status === 'completed' ? (
                      <><CheckCircle className="w-4 h-4 text-emerald-600" /> 已完成</>
                    ) : (
                      <><Clock className="w-4 h-4 text-slate-400" /> 未生成</>
                    )}
                  </div>
                </div>
                <div className={`
                  p-4 rounded-xl border transition-all
                  ${design?.status === 'completed'
                    ? 'bg-emerald-50 border-emerald-200'
                    : 'bg-slate-50 border-slate-200'
                  }
                `}>
                  <div className="text-sm text-slate-500 mb-1">测试设计</div>
                  <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                    {design?.status === 'completed' ? (
                      <><CheckCircle className="w-4 h-4 text-emerald-600" /> 已完成</>
                    ) : strategy?.status === 'completed' ? (
                      <><Clock className="w-4 h-4 text-slate-400" /> 可生成</>
                    ) : (
                      <><AlertCircle className="w-4 h-4 text-amber-500" /> 需先完成策略</>
                    )}
                  </div>
                </div>
                <div className={`
                  p-4 rounded-xl border transition-all
                  ${cases?.status === 'completed'
                    ? 'bg-emerald-50 border-emerald-200'
                    : 'bg-slate-50 border-slate-200'
                  }
                `}>
                  <div className="text-sm text-slate-500 mb-1">测试用例</div>
                  <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                    {cases?.status === 'completed' ? (
                      <><CheckCircle className="w-4 h-4 text-emerald-600" /> 已完成</>
                    ) : design?.status === 'completed' ? (
                      <><Clock className="w-4 h-4 text-slate-400" /> 可生成</>
                    ) : (
                      <><AlertCircle className="w-4 h-4 text-amber-500" /> 需先完成设计</>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'strategy' && strategy?.content && (
            renderContentBlock(strategy.content)
          )}

          {activeTab === 'design' && design?.content && (
            renderContentBlock(design.content)
          )}

          {activeTab === 'cases' && cases?.content && (
            renderContentBlock(cases.content)
          )}

          {activeTab === 'lecroy' && (
            <div className="space-y-5 animate-[fadeIn_0.3s_ease-out]">
              {/* 自然语言输入区域 */}
              <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
                <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-blue-600" />
                  自然语言生成 LeCroy 脚本
                </h3>
                {/* 生成模式选择 */}
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xs text-slate-500">生成模式:</span>
                  {(['template', 'llm', 'hybrid'] as const).map((m) => (
                    <button
                      key={m}
                      onClick={() => setGenerationMode(m)}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                        generationMode === m
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      {m === 'template' ? '模板引擎' : m === 'llm' ? 'AI 生成' : '混合模式'}
                    </button>
                  ))}
                  <span className="text-xs text-slate-400 ml-1">
                    {generationMode === 'template' && '快速可靠，场景有限'}
                    {generationMode === 'llm' && '智能灵活，消耗 API'}
                    {generationMode === 'hybrid' && '模板打底 + AI 优化，推荐'}
                  </span>
                </div>
                <div className="space-y-3">
                  <input
                    type="text"
                    value={lecroyTestName}
                    onChange={(e) => setLecroyTestName(e.target.value)}
                    placeholder="测试名称（可选，如: CXL_MemRd_Test）"
                    className="w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
                  />
                  <textarea
                    value={lecroyDescription}
                    onChange={(e) => setLecroyDescription(e.target.value)}
                    placeholder="请用自然语言描述测试步骤，例如：&#10;1. 初始化 CXL 链路&#10;2. 发送 M2S 内存读取请求到地址 0x1000&#10;3. 等待 S2M 响应并验证数据完整性&#10;4. 检查链路层 CRC 是否正确"
                    rows={6}
                    className="w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm resize-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all font-mono"
                  />
                  <button
                    onClick={generateLecroyScript}
                    disabled={generatingScript || !lecroyDescription.trim()}
                    className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
                  >
                    <FileCode className="w-4 h-4" />
                    {generatingScript ? '生成中（约需1-3分钟）...' : '生成 PEG + PEVS 脚本'}
                  </button>
                </div>
              </div>

              {/* 脚本列表 */}
              {lecroyScripts.length === 0 ? (
                <div className="text-center py-12 text-slate-500 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
                  <Terminal className="w-10 h-10 mx-auto mb-3 text-slate-300" />
                  暂无生成的 LeCroy 脚本
                  <p className="text-xs text-slate-400 mt-1">在上方输入测试步骤描述即可生成</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="text-sm text-slate-500 mb-2 font-medium">
                    共 {lecroyScripts.length} 个脚本
                  </div>
                  {(() => {
                    const totalPages = Math.max(1, Math.ceil(lecroyScripts.length / SCRIPTS_PER_PAGE))
                    const start = (scriptListPage - 1) * SCRIPTS_PER_PAGE
                    const pageScripts = lecroyScripts.slice(start, start + SCRIPTS_PER_PAGE)
                    return (
                      <>
                        {pageScripts.map((script) => (
                          <div
                            key={script.id}
                            className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100 hover:bg-white hover:shadow-md hover:border-slate-200 transition-all"
                          >
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-slate-800">{script.test_name}</div>
                              <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                                {script.protocol && (
                                  <span className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">{script.protocol}</span>
                                )}
                                {script.scenario && (
                                  <span className="text-xs bg-purple-50 text-purple-600 px-1.5 py-0.5 rounded">{script.scenario}</span>
                                )}
                                {script.generation_mode && (
                                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                                    script.generation_mode === 'llm' ? 'bg-emerald-50 text-emerald-600' :
                                    script.generation_mode === 'hybrid' ? 'bg-amber-50 text-amber-600' :
                                    script.generation_mode === 'llm_optimized' ? 'bg-pink-50 text-pink-600' :
                                    'bg-slate-100 text-slate-500'
                                  }`}>
                                    {script.generation_mode === 'llm' ? 'AI生成' :
                                     script.generation_mode === 'hybrid' ? '混合' :
                                     script.generation_mode === 'llm_optimized' ? 'AI优化' :
                                     '模板'}
                                  </span>
                                )}
                                <span className="text-xs text-slate-400">
                                  {new Date(script.created_at).toLocaleString()}
                                </span>
                              </div>
                            </div>
                            <div className="flex items-center gap-2 ml-3">
                              <button
                                onClick={() => viewScript(script.id)}
                                className="px-4 py-2 bg-blue-50 text-blue-700 rounded-xl hover:bg-blue-100 text-sm font-medium transition-colors"
                              >
                                查看
                              </button>
                              <button
                                onClick={() => deleteScript(script.id)}
                                className="p-2 text-red-500 hover:bg-red-50 rounded-xl transition-colors"
                                title="删除"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))}
                        {totalPages > 1 && (
                          <div className="flex items-center justify-center gap-2 pt-3">
                            <button
                              onClick={() => setScriptListPage(1)}
                              disabled={scriptListPage <= 1}
                              className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                            >
                              首页
                            </button>
                            <button
                              onClick={() => setScriptListPage(p => Math.max(1, p - 1))}
                              disabled={scriptListPage <= 1}
                              className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                            >
                              上一页
                            </button>
                            <span className="text-xs text-slate-500 px-2">{scriptListPage} / {totalPages}</span>
                            <button
                              onClick={() => setScriptListPage(p => Math.min(totalPages, p + 1))}
                              disabled={scriptListPage >= totalPages}
                              className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                            >
                              下一页
                            </button>
                            <button
                              onClick={() => setScriptListPage(totalPages)}
                              disabled={scriptListPage >= totalPages}
                              className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                            >
                              末页
                            </button>
                          </div>
                        )}
                      </>
                    )
                  })()}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 脚本详情 Modal */}
      {showScriptModal && selectedScript && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-[fadeIn_0.2s_ease-out]">
          <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col animate-[slideUp_0.3s_ease-out] overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-slate-100">
              <div>
                <h3 className="font-semibold text-slate-800">{selectedScript.test_name}</h3>
                <div className="flex items-center gap-2 mt-1">
                  {selectedScript.protocol && (
                    <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{selectedScript.protocol}</span>
                  )}
                  {selectedScript.scenario && (
                    <span className="text-xs bg-purple-50 text-purple-600 px-2 py-0.5 rounded-full">{selectedScript.scenario}</span>
                  )}
                  {selectedScript.generation_mode && (
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      selectedScript.generation_mode === 'llm' ? 'bg-emerald-50 text-emerald-600' :
                      selectedScript.generation_mode === 'hybrid' ? 'bg-amber-50 text-amber-600' :
                      selectedScript.generation_mode === 'llm_optimized' ? 'bg-pink-50 text-pink-600' :
                      'bg-slate-100 text-slate-500'
                    }`}>
                      {selectedScript.generation_mode === 'llm' ? 'AI 生成' :
                       selectedScript.generation_mode === 'hybrid' ? '混合模式' :
                       selectedScript.generation_mode === 'llm_optimized' ? 'AI 优化' :
                       '模板引擎'}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={() => setShowScriptModal(false)}
                className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-auto p-6 space-y-6">
              {selectedScript.description && (
                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                  <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">原始描述</h4>
                  <p className="text-sm text-slate-700 whitespace-pre-wrap">{selectedScript.description}</p>
                </div>
              )}

              {/* 优化历史 */}
              {selectedScript.feedback_history && selectedScript.feedback_history.length > 0 && (
                <div className="bg-amber-50 rounded-xl p-4 border border-amber-100">
                  <h4 className="text-xs font-semibold text-amber-600 uppercase tracking-wider mb-2">优化历史</h4>
                  <div className="space-y-2">
                    {selectedScript.feedback_history.map((h, i) => (
                      <div key={i} className="text-sm">
                        <div className="text-amber-700 font-medium">{i + 1}. {h.feedback}</div>
                        {h.reasoning && (
                          <div className="text-amber-600/70 text-xs mt-0.5">{h.reasoning}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedScript.peg_content && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-slate-700">PEG 训练脚本</h4>
                    <div className="flex gap-2">
                      <button
                        onClick={() => copyToClipboard(selectedScript.peg_content || '')}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                      >
                        <ClipboardCopy className="w-3.5 h-3.5" />
                        复制
                      </button>
                      <button
                        onClick={() => downloadFile(selectedScript.peg_content || '', `${selectedScript.test_name || 'script'}.peg`)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 rounded-lg hover:bg-emerald-100 transition-colors"
                      >
                        <FileCode className="w-3.5 h-3.5" />
                        下载 .peg
                      </button>
                    </div>
                  </div>
                  {(() => {
                    const lines = (selectedScript.peg_content || '').split('\n')
                    const totalPages = Math.max(1, Math.ceil(lines.length / SCRIPT_LINES_PER_PAGE))
                    const start = (pegPage - 1) * SCRIPT_LINES_PER_PAGE
                    const pageContent = lines.slice(start, start + SCRIPT_LINES_PER_PAGE).join('\n')
                    return (
                      <>
                        <pre className="whitespace-pre-wrap font-mono text-sm bg-slate-900 text-slate-100 p-5 rounded-xl overflow-x-auto min-h-[200px]">
                          {pageContent}
                        </pre>
                        {totalPages > 1 && (
                          <div className="flex items-center justify-between mt-3 px-1">
                            <div className="text-xs text-slate-500">
                              共 {lines.length} 行，第 {pegPage} / {totalPages} 页
                            </div>
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => setPegPage(1)}
                                disabled={pegPage <= 1}
                                className="px-2 py-1 text-xs rounded bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                              >
                                首页
                              </button>
                              <button
                                onClick={() => setPegPage(p => Math.max(1, p - 1))}
                                disabled={pegPage <= 1}
                                className="px-2 py-1 text-xs rounded bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                              >
                                上一页
                              </button>
                              <span className="text-xs text-slate-500 px-2">{pegPage} / {totalPages}</span>
                              <button
                                onClick={() => setPegPage(p => Math.min(totalPages, p + 1))}
                                disabled={pegPage >= totalPages}
                                className="px-2 py-1 text-xs rounded bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                              >
                                下一页
                              </button>
                              <button
                                onClick={() => setPegPage(totalPages)}
                                disabled={pegPage >= totalPages}
                                className="px-2 py-1 text-xs rounded bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                              >
                                末页
                              </button>
                            </div>
                          </div>
                        )}
                      </>
                    )
                  })()}
                </div>
              )}
              {selectedScript.pevs_content && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-slate-700">PEVS 验证脚本</h4>
                    <div className="flex gap-2">
                      <button
                        onClick={() => copyToClipboard(selectedScript.pevs_content || '')}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                      >
                        <ClipboardCopy className="w-3.5 h-3.5" />
                        复制
                      </button>
                      <button
                        onClick={() => downloadFile(selectedScript.pevs_content || '', `${selectedScript.test_name || 'script'}.pevs`)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 rounded-lg hover:bg-emerald-100 transition-colors"
                      >
                        <FileCode className="w-3.5 h-3.5" />
                        下载 .pevs
                      </button>
                    </div>
                  </div>
                  {(() => {
                    const lines = (selectedScript.pevs_content || '').split('\n')
                    const totalPages = Math.max(1, Math.ceil(lines.length / SCRIPT_LINES_PER_PAGE))
                    const start = (pevsPage - 1) * SCRIPT_LINES_PER_PAGE
                    const pageContent = lines.slice(start, start + SCRIPT_LINES_PER_PAGE).join('\n')
                    return (
                      <>
                        <pre className="whitespace-pre-wrap font-mono text-sm bg-slate-900 text-slate-100 p-5 rounded-xl overflow-x-auto min-h-[200px]">
                          {pageContent}
                        </pre>
                        {totalPages > 1 && (
                          <div className="flex items-center justify-between mt-3 px-1">
                            <div className="text-xs text-slate-500">
                              共 {lines.length} 行，第 {pevsPage} / {totalPages} 页
                            </div>
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => setPevsPage(1)}
                                disabled={pevsPage <= 1}
                                className="px-2 py-1 text-xs rounded bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                              >
                                首页
                              </button>
                              <button
                                onClick={() => setPevsPage(p => Math.max(1, p - 1))}
                                disabled={pevsPage <= 1}
                                className="px-2 py-1 text-xs rounded bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                              >
                                上一页
                              </button>
                              <span className="text-xs text-slate-500 px-2">{pevsPage} / {totalPages}</span>
                              <button
                                onClick={() => setPevsPage(p => Math.min(totalPages, p + 1))}
                                disabled={pevsPage >= totalPages}
                                className="px-2 py-1 text-xs rounded bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                              >
                                下一页
                              </button>
                              <button
                                onClick={() => setPevsPage(totalPages)}
                                disabled={pevsPage >= totalPages}
                                className="px-2 py-1 text-xs rounded bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                              >
                                末页
                              </button>
                            </div>
                          </div>
                        )}
                      </>
                    )
                  })()}
                </div>
              )}

              {/* 优化反馈区域 */}
              <div className="border-t border-slate-200 pt-5">
                <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 text-blue-600" />
                  AI 优化脚本
                </h4>
                <p className="text-xs text-slate-500 mb-2">对当前脚本不满意？输入优化建议，AI 将基于现有脚本生成改进版本。</p>
                <div className="flex gap-2">
                  <textarea
                    value={optimizeFeedback}
                    onChange={(e) => setOptimizeFeedback(e.target.value)}
                    placeholder="例如：请在PEVS中添加链路宽度变化的验证步骤；或者：PEG中增加热复位后的延迟时间到5秒..."
                    rows={2}
                    className="flex-1 px-3 py-2 border border-slate-200 rounded-xl text-sm resize-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
                  />
                  <button
                    onClick={optimizeScript}
                    disabled={optimizing || !optimizeFeedback.trim()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm self-end"
                  >
                    {optimizing ? '优化中...' : '提交优化'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectDetail
