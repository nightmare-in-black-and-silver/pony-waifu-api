from pathlib import Path


class Config:
    def __init__(self):
        self.root_dir = Path(__file__).resolve().parent.parent
        self.configuration_dir = self.root_dir / "configuration"
        
        self.cast_file = self.configuration_dir / "cast.json"
        self.api_file = self.configuration_dir / "api.json"
        self.user_file = self.configuration_dir / "user.json"
        self.prompts_file = self.configuration_dir / "prompts.json"