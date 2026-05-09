import { FC, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, FolderOpen, ChevronRight, HardDrive, Cpu, Zap, Search, X } from 'lucide-react'
import axios from 'axios'

interface Project {
  id: number
  name: string
  device_type: string
  status: string
  created_at: string
}

const deviceIcons: Record<string, React.ReactNode> = {
  SSD: <HardDrive className="w-5 h-5" />,
  CXL: <Cpu className="w-5 h-5" />,
  PCM: <Zap className="w-5 h-5" />,
}

const deviceColors: Record<string, string> = {
  SSD: 'from-emerald-500 to-teal-600',
  CXL: 'from-blue-500 to-indigo-600',
  PCM: 'from-amber-500 to-orange-600',
}

const statusConfig: Record<string, { label: string; class: string; dot: string }> = {
  created: { label: '已创建', class: 'bg-slate-100 text-slate-600', dot: 'bg-slate-400' },
  completed: { label: '已完成', class: 'bg-emerald-50 text-emerald-700 border border-emerald-200', dot: 'bg-emerald-500' },
  strategy_generating: { label: '生成策略中', class: 'bg-blue-50 text-blue-700 border border-blue-200', dot: 'bg-blue-500 animate-pulse' },
  design_generating: { label: '生成设计中', class: 'bg-amber-50 text-amber-700 border border-amber-200', dot: 'bg-amber-500 animate-pulse' },
  cases_generating: { label: '生成用例中', class: 'bg-purple-50 text-purple-700 border border-purple-200', dot: 'bg-purple-500 animate-pulse' },
  cancelled: { label: '已取消', class: 'bg-red-50 text-red-700 border border-red-200', dot: 'bg-red-500' },
}

const ProjectList: FC = () => {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [search, setSearch] = useState('')
  const [newProject, setNewProject] = useState({ name: '', device_type: 'SSD', requirements: '' })

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      const res = await axios.get('/api/projects')
      setProjects(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const createProject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newProject.name.trim()) return
    try {
      await axios.post('/api/projects', newProject)
      setShowForm(false)
      setNewProject({ name: '', device_type: 'SSD', requirements: '' })
      fetchProjects()
    } catch (err) {
      console.error(err)
    }
  }

  const filteredProjects = projects.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.device_type.toLowerCase().includes(search.toLowerCase())
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">项目列表</h1>
          <p className="text-sm text-slate-500 mt-1">管理您的存储设备测试项目</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="btn-primary inline-flex items-center justify-center gap-2 self-start"
        >
          <Plus className="w-4 h-4" />
          新建项目
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          placeholder="搜索项目..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-10 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
        />
        {search && (
          <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Create Form */}
      {showForm && (
        <div className="glass-card p-6 mb-6 animate-slide-up">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">新建测试项目</h2>
          <form onSubmit={createProject} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">项目名称</label>
                <input
                  type="text"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
                  placeholder="例如：企业级 NVMe SSD 测试"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">设备类型</label>
                <select
                  value={newProject.device_type}
                  onChange={(e) => setNewProject({ ...newProject, device_type: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
                >
                  <option value="SSD">SSD (固态硬盘)</option>
                  <option value="CXL">CXL Memory (内存扩展)</option>
                  <option value="PCM">PCM (相变存储)</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">初始需求（可选）</label>
              <textarea
                value={newProject.requirements}
                onChange={(e) => setNewProject({ ...newProject, requirements: e.target.value })}
                className="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all resize-none"
                rows={3}
                placeholder="简要描述测试需求..."
              />
            </div>
            <div className="flex gap-3 pt-2">
              <button type="submit" className="btn-primary">创建项目</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">取消</button>
            </div>
          </form>
        </div>
      )}

      {/* Project List */}
      <div className="space-y-3">
        {filteredProjects.length === 0 ? (
          <div className="glass-card py-16 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center">
              <FolderOpen className="w-8 h-8 text-slate-400" />
            </div>
            <p className="text-slate-500 font-medium">{search ? '未找到匹配的项目' : '暂无项目，点击上方按钮创建'}</p>
          </div>
        ) : (
          filteredProjects.map((project) => {
            const status = statusConfig[project.status] || statusConfig.created
            const colorClass = deviceColors[project.device_type] || deviceColors.SSD
            return (
              <Link
                key={project.id}
                to={`/projects/${project.id}`}
                className="group flex items-center gap-4 p-4 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-lg hover:shadow-slate-200/50 hover:border-slate-200 transition-all duration-300"
              >
                {/* Icon */}
                <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${colorClass} flex items-center justify-center shadow-lg shadow-slate-200/50 text-white shrink-0`}>
                  {deviceIcons[project.device_type] || deviceIcons.SSD}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-slate-800 truncate group-hover:text-blue-600 transition-colors">{project.name}</h3>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-slate-400">{project.device_type}</span>
                    <span className="text-slate-300">·</span>
                    <span className="text-xs text-slate-400">{new Date(project.created_at).toLocaleDateString('zh-CN')}</span>
                  </div>
                </div>

                {/* Status */}
                <div className={`status-badge ${status.class}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`} />
                  {status.label}
                </div>

                <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-blue-500 group-hover:translate-x-0.5 transition-all shrink-0" />
              </Link>
            )
          })
        )}
      </div>
    </div>
  )
}

export default ProjectList
