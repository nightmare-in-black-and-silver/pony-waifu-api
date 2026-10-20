from pathlib import Path


class Config:
    def __init__(self):
        self.root_dir = Path(__file__).resolve().parent.parent
        self.configuration_dir = self.root_dir / "configuration"
        self.expression_files_dir = self.root_dir / "assets" / "expressions"
        
        self.cast_file = self.configuration_dir / "cast.json"
        self.anatomy_file = self.configuration_dir / "anatomy.json"
        self.expressions_file = self.configuration_dir / "expressions.json"
        self.llm_endpoints_file = self.configuration_dir / "llm_endpoints.json"
        self.user_file = self.configuration_dir / "user.json"
        self.instruction_template_file = self.configuration_dir / "instruction_templates.json"
        self.scene_mood_file = self.configuration_dir / "scene_mood.json"