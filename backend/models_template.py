from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from datetime import datetime
from backend.database import Base

class TestTemplate(Base):
    __tablename__ = "test_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_key = Column(String(100), unique=True, nullable=False, index=True)
    template_type = Column(String(50), nullable=False)  # strategy, design, case
    scope = Column(String(50), default="global")  # global, project
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Mustache template content
    structure = Column(JSON, nullable=True)  # Template structure definition
    tags = Column(JSON, default=list)  # Array of tags
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TemplateVariable(Base):
    __tablename__ = "template_variables"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, nullable=False)
    var_name = Column(String(100), nullable=False)
    var_type = Column(String(50), default="string")  # string, number, boolean, array, object
    description = Column(String(500), nullable=True)
    default_value = Column(Text, nullable=True)
    is_required = Column(Boolean, default=False)