import chevron
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models_template import TestTemplate
from backend.database import SessionLocal

class TemplateManager:
    """Mustache模板管理器"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
    
    def render(self, template_content: str, variables: Dict[str, Any]) -> str:
        """渲染Mustache模板"""
        try:
            return chevron.render(template_content, variables)
        except Exception as e:
            raise ValueError(f"Template rendering error: {str(e)}")
    
    def render_by_key(self, template_key: str, variables: Dict[str, Any]) -> str:
        """通过模板键渲染模板"""
        template = self.db.query(TestTemplate).filter(
            TestTemplate.template_key == template_key,
            TestTemplate.is_active == True
        ).first()
        
        if not template:
            raise ValueError(f"Template not found: {template_key}")
        
        return self.render(template.content, variables)
    
    def get_template(self, template_key: str) -> Optional[TestTemplate]:
        """获取模板"""
        return self.db.query(TestTemplate).filter(
            TestTemplate.template_key == template_key
        ).first()
    
    def list_templates(self, template_type: str = None, scope: str = None) -> List[TestTemplate]:
        """列出模板"""
        query = self.db.query(TestTemplate)
        
        if template_type:
            query = query.filter(TestTemplate.template_type == template_type)
        if scope:
            query = query.filter(TestTemplate.scope == scope)
        
        return query.all()
    
    def create_template(self, template_data: Dict[str, Any]) -> TestTemplate:
        """创建模板"""
        template = TestTemplate(**template_data)
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def update_template(self, template_id: int, template_data: Dict[str, Any]) -> Optional[TestTemplate]:
        """更新模板"""
        template = self.db.query(TestTemplate).filter(TestTemplate.id == template_id).first()
        if not template:
            return None
        
        for key, value in template_data.items():
            setattr(template, key, value)
        
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def delete_template(self, template_id: int) -> bool:
        """删除模板"""
        template = self.db.query(TestTemplate).filter(TestTemplate.id == template_id).first()
        if not template:
            return False
        
        self.db.delete(template)
        self.db.commit()
        return True

# 全局模板管理器实例
template_manager = TemplateManager()