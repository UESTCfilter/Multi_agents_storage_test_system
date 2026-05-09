import { FC } from 'react'
import { Outlet, Link } from 'react-router-dom'
import { Database, Sparkles } from 'lucide-react'

const Layout: FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white/70 backdrop-blur-xl border-b border-slate-200/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-3 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/30 transition-shadow">
                <Database className="w-5 h-5 text-white" />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                  AI 存储测试系统
                </span>
                <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 text-[10px] font-bold text-blue-700 uppercase tracking-wider">
                  <Sparkles className="w-3 h-3" />
                  v2.0
                </span>
              </div>
            </Link>

            <div className="flex items-center gap-3">
              <a
                href="http://localhost:8001/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="hidden sm:flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-blue-600 transition-colors"
              >
                API 文档
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200/60 bg-white/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400">
            <span>AI Storage Test System v2.0 — 智能测试策略生成平台</span>
            <span>Powered by Kimi K2.5 · 30 专家集群</span>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout
