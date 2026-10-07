from pathlib import Path


class Config:
    def __init__(self):
        self.root_dir = Path(__file__).resolve().parent.parent
        self.configuration_dir = self.root_dir / "configuration"
        self.cast_file = self.configuration_dir / "cast.json"