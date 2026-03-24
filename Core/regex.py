# Core/regex.py
import re

class AutoRegexEngine:
    @staticmethod
    def generate_rules(transitions_names, raw_all_names):
        """
        Analyse mathématiquement les noms bruts et renvoie une liste de dictionnaires de règles.
        """
        total_trans = len(transitions_names)
        active_names = list(transitions_names)
        new_rules = []
        parent_roots = set()

        def apply_rules(names, rule):
            res = []
            for n in names:
                try:
                    curr = re.sub(rule["pattern"], rule["replacement"], n)
                    res.append(curr.strip())
                except:
                    res.append(n)
            return res

        # ==========================================
        # ÉTAGE 1 : LES GROUPES PARENTS ABSOLUS
        # ==========================================
        parent_threshold = max(2, int(total_trans * 0.03)) # ~3% minimum
        
        prefix_counts = {}
        for name in active_names:
            match = re.match(r"^([A-Za-z]+)([\.\s])", name)
            if match:
                p_word = match.group(1)
                p_sep = match.group(2)
                key = (p_word, p_sep)
                prefix_counts[key] = prefix_counts.get(key, 0) + 1
        
        for (p_word, p_sep), count in sorted(prefix_counts.items(), key=lambda x: x[1], reverse=True):
            if count >= parent_threshold:
                parent_roots.add(p_word)
                safe_sep = r"\." if p_sep == "." else r"\ "
                pattern = r"^" + p_word + safe_sep
                
                rule = {"type": "Transition", "pattern": pattern, "replacement": ""}
                new_rules.append(rule)
                active_names = apply_rules(active_names, rule)

        # ==========================================
        # ÉTAGE 2 : LES PLUGINS ET RÉSIDUS
        # ==========================================
        plugin_threshold = 3
        plugin_counts = {}
        for name in active_names:
            match = re.match(r"^([A-Za-z]+)[0-9]*[\.\s_]*", name)
            if match:
                root = match.group(1)
                plugin_counts[root] = plugin_counts.get(root, 0) + 1
                
        for root, count in sorted(plugin_counts.items(), key=lambda x: x[1], reverse=True):
            if count >= plugin_threshold:
                pattern = r"^" + root + r"[0-9]*[\.\s_]*"
                
                if root in parent_roots:
                    replacement = " "
                else:
                    replacement = f"{root} "
                    
                rule = {"type": "Transition", "pattern": pattern, "replacement": replacement}
                if not any(r["pattern"] == rule["pattern"] for r in new_rules):
                    new_rules.append(rule)
                    active_names = apply_rules(active_names, rule)

        # ==========================================
        # ÉTAGE 3 : LES SOUS-GROUPES FLOTTANTS
        # ==========================================
        floating_counts = {}
        for name in active_names:
            match = re.search(r"([A-Za-z]+)_", name)
            if match:
                f = match.group(1)
                floating_counts[f] = floating_counts.get(f, 0) + 1
                
        for f, count in sorted(floating_counts.items(), key=lambda x: x[1], reverse=True):
            if count >= plugin_threshold:
                pattern = f + r"_"
                replacement = f"{f} "
                
                rule = {"type": "Transition", "pattern": pattern, "replacement": replacement}
                if not any(r["pattern"] == rule["pattern"] for r in new_rules):
                    new_rules.append(rule)
                    active_names = apply_rules(active_names, rule)

        # ==========================================
        # ÉTAGE 4 : ANOMALIES DE FIN (Ex: PrTr)
        # ==========================================
        suffix_counts = {}
        for name in active_names:
            match = re.search(r"[a-z]([A-Z][a-zA-Z]+)$", name)
            if match:
                s = match.group(1)
                suffix_counts[s] = suffix_counts.get(s, 0) + 1
                
        for s, count in sorted(suffix_counts.items(), key=lambda x: x[1], reverse=True):
            if count >= plugin_threshold:
                pattern = s + r"$"
                rule = {"type": "Transition", "pattern": pattern, "replacement": ""}
                
                if not any(r["pattern"] == rule["pattern"] for r in new_rules):
                    new_rules.append(rule)
                    active_names = apply_rules(active_names, rule)

        return new_rules