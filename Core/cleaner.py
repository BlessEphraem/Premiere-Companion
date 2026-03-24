import re
import json
import os
from Core.paths import get_data_path

class EffectCleaner:
    def __init__(self):
        self.rules_path = get_data_path("rules.json")
        self.rules = []
        self.load_rules()

    def load_rules(self):
        if os.path.exists(self.rules_path):
            try:
                with open(self.rules_path, "r", encoding="utf-8") as f:
                    self.rules = json.load(f)
            except Exception:
                self.rules = []
        else:
            self.rules = []
            os.makedirs(get_data_path(), exist_ok=True)
            self.save_rules()

    def save_rules(self, new_rules=None):
        if new_rules is not None:
            self.rules = new_rules
        with open(self.rules_path, "w", encoding="utf-8") as f:
            json.dump(self.rules, f, indent=4)

    def clean_name(self, raw_name, effect_type):
        if not raw_name: 
            return "Unnamed"
            
        name = raw_name
        
        for rule in self.rules:
            rule_type = rule.get("type")
            
            if rule_type and rule_type not in effect_type:
                continue
                
            pattern = rule.get("pattern")
            replacement = rule.get("replacement", "")
            
            if pattern:
                try:
                    name = re.sub(pattern, replacement, name)
                except:
                    pass

        name = re.sub(r' {2,}', ' ', name).strip()
        
        return name if name else raw_name