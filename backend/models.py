from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    device_type = Column(String(50), nullable=False)  # SSD, CXL, etc.
    requirements = Column(Text, nullable=True)
    test_objective = Column(String(255), nullable=True)
    target_market = Column(String(100), nullable=True)
    current_stage = Column(String(50), default="idle")
    status = Column(String(50), default="created")  # created, strategy_ready, design_ready, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    deliverables = relationship("Deliverable", back_populates="project", cascade="all, delete-orphan")
    agent_logs = relationship("AgentLog", back_populates="project", cascade="all, delete-orphan")

class Deliverable(Base):
    __tablename__ = "deliverables"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    type = Column(String(50), nullable=False)  # strategy, design, case
    content = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, generating, completed, error
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="deliverables")

class AgentLog(Base):
    __tablename__ = "agent_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    task_type = Column(String(50), nullable=False)  # strategy, design, case
    status = Column(String(50), default="running")  # running, completed, error
    output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # 关系
    project = relationship("Project", back_populates="agent_logs")

class WorkflowState(Base):
    __tablename__ = "workflow_states"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), unique=True, nullable=False)
    status = Column(String(50), default="idle")  # idle, running, completed, error
    current_stage = Column(String(50), nullable=True)  # strategy, design, case
    progress = Column(Integer, default=0)  # 0-100
    message = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Template(Base):
    """模板管理表 - 支持默认模板和用户自定义模板"""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    type = Column(String(50), nullable=False)  # strategy, design, case
    content = Column(Text, nullable=False)  # 模板内容（Markdown格式）
    is_default = Column(Boolean, default=False)  # 是否为系统默认模板
    is_editable = Column(Boolean, default=True)  # 是否可编辑（默认模板可编辑副本）
    parent_id = Column(Integer, ForeignKey("templates.id"), nullable=True)  # 继承自哪个模板
    created_by = Column(String(100), default="system")  # system 或 user_id
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    parent = relationship("Template", remote_side=[id], backref="children")


class LeCroyScript(Base):
    """LeCroy 脚本表 - 保存生成的 PEG/PEVS 脚本"""
    __tablename__ = "lecroy_scripts"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    test_name = Column(String(200), nullable=False)
    protocol = Column(String(50), nullable=True)
    scenario = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)  # 用户输入的自然语言描述
    peg_content = Column(Text, nullable=False)  # PEG 脚本内容
    pevs_content = Column(Text, nullable=False)  # PEVS 脚本内容
    generation_mode = Column(String(20), default="template")  # template / llm
    feedback_history = Column(JSON, default=list)  # 优化历史记录 [{feedback, timestamp, reasoning}]
    optimized_from = Column(Integer, ForeignKey("lecroy_scripts.id"), nullable=True)  # 基于哪个脚本优化
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)