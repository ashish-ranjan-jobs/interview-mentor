import glob
import re
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from app.config import AGENTS_DIR

CATEGORY_META = {
    "systems-design": {
        "title": "Systems Design",
        "description": "Architect scalable, distributed, fault-tolerant infrastructure and APIs.",
        "badge": "Architecture",
        "color": "indigo",
        "icon": "fa-server",
    },
    "swe-i": {
        "title": "SWE-I (Entry Level)",
        "description": "Foundational data structures, two pointers, sliding window, and recursion.",
        "badge": "Core DS & Algo",
        "color": "emerald",
        "icon": "fa-code",
    },
    "swe-ii": {
        "title": "SWE-II (Mid/Senior)",
        "description": "Dynamic programming, graph algorithms, concurrency, and advanced heaps.",
        "badge": "Advanced Algorithms",
        "color": "blue",
        "icon": "fa-laptop-code",
    },
    "debugging": {
        "title": "Production Debugging",
        "description": "Diagnose memory leaks, slow queries, broken APIs, and cascading failures.",
        "badge": "Troubleshooting",
        "color": "rose",
        "icon": "fa-bug",
    },
    "devops-sre": {
        "title": "DevOps & SRE",
        "description": "Kubernetes orchestration, CI/CD pipelines, observability, and alerting.",
        "badge": "Infrastructure",
        "color": "amber",
        "icon": "fa-cloud",
    },
    "data-engineer": {
        "title": "Data Engineering",
        "description": "Pipeline architecture, SQL query tuning, lakehouse schema, and MySQL indexing.",
        "badge": "Data & ETL",
        "color": "cyan",
        "icon": "fa-database",
    },
    "behavioral": {
        "title": "Behavioral & Leadership",
        "description": "Amazon LP, STAR method, conflict resolution, ownership, and learning from failure.",
        "badge": "Soft Skills & Culture",
        "color": "purple",
        "icon": "fa-users",
    },
    "ai-pm": {
        "title": "AI Product Management",
        "description": "Prompt architecture, AI product strategy, evaluation frameworks, and AI ethics.",
        "badge": "AI Strategy",
        "color": "fuchsia",
        "icon": "fa-brain",
    },
    "ml-engineer": {
        "title": "Machine Learning Engineer",
        "description": "Deep learning theory, backpropagation, and large-scale ML systems design.",
        "badge": "AI & Deep Learning",
        "color": "violet",
        "icon": "fa-microchip",
    },
    "frontend": {
        "title": "Frontend Engineering",
        "description": "React lifecycle, event loop, rendering pipelines, and DOM performance.",
        "badge": "Web & UI",
        "color": "teal",
        "icon": "fa-desktop",
    },
    "meta": {
        "title": "Meta & Problem Solving",
        "description": "Deconstructing ambiguous problems, scoping, and trade-off synthesis.",
        "badge": "Problem Framing",
        "color": "orange",
        "icon": "fa-lightbulb",
    },
}


class SkillCatalog:
    def __init__(self, agents_dir: Path = AGENTS_DIR):
        self.agents_dir = agents_dir
        self.skills: Dict[str, dict] = {}
        self.reload()

    def reload(self):
        skills_map = {}
        for path in glob.glob(str(self.agents_dir / "**" / "SKILL.md"), recursive=True):
            p = Path(path)
            rel = p.relative_to(self.agents_dir)
            category = rel.parts[0]
            folder = rel.parts[1] if len(rel.parts) > 1 else ''
            skill_id = folder or p.parent.name

            try:
                with open(p, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                continue

            frontmatter = {}
            body = content
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                        body = parts[2]
                    except Exception:
                        pass

            title_m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            title = title_m.group(1).strip() if title_m else frontmatter.get("name", skill_id)

            role_m = re.search(r">\s*\*\*Target Role\*\*:\s*(.+)$", body, re.MULTILINE)
            diff_m = re.search(r">\s*\*\*Difficulty\*\*:\s*(.+)$", body, re.MULTILINE)
            topic_m = re.search(r">\s*\*\*Topic\*\*:\s*(.+)$", body, re.MULTILINE)

            cat_info = CATEGORY_META.get(category, {
                "title": category.replace("-", " ").title(),
                "description": "",
                "badge": category.upper(),
                "color": "slate",
                "icon": "fa-terminal",
            })

            skills_map[skill_id] = {
                "id": skill_id,
                "name": frontmatter.get("name", skill_id),
                "title": title,
                "category": category,
                "category_title": cat_info["title"],
                "category_badge": cat_info["badge"],
                "category_color": cat_info["color"],
                "category_icon": cat_info["icon"],
                "role": role_m.group(1).strip() if role_m else "Software Engineer",
                "difficulty": diff_m.group(1).strip() if diff_m else "Medium",
                "topic": topic_m.group(1).strip() if topic_m else cat_info["title"],
                "description": frontmatter.get("description", "").strip(),
                "path": str(p),
                "raw_content": content,
                "body_content": body,
            }

        self.skills = skills_map

    def list_skills(self, category: Optional[str] = None, search: Optional[str] = None) -> List[dict]:
        results = list(self.skills.values())
        if category and category != "all":
            results = [s for s in results if s["category"] == category]
        if search:
            q = search.lower().strip()
            results = [
                s for s in results
                if q in s["title"].lower() or q in s["description"].lower() or q in s["role"].lower() or q in s["topic"].lower()
            ]
        # Sort by category title, then skill title
        results.sort(key=lambda s: (s["category"], s["title"]))
        return results

    def get_skill(self, skill_id: str) -> Optional[dict]:
        return self.skills.get(skill_id)

    def get_categories(self) -> List[dict]:
        cats = []
        for cat_id, meta in CATEGORY_META.items():
            count = len([s for s in self.skills.values() if s["category"] == cat_id])
            if count > 0:
                cats.append({
                    "id": cat_id,
                    "title": meta["title"],
                    "description": meta["description"],
                    "badge": meta["badge"],
                    "color": meta["color"],
                    "icon": meta["icon"],
                    "count": count,
                })
        return cats

    def build_system_prompt(self, skill_id: str, custom_instructions: Optional[str] = None) -> str:
        skill = self.get_skill(skill_id)
        if not skill:
            return "You are an expert technical interviewer conducting a mock interview."

        system_prompt = f"""You are conducting an interactive, professional mock interview.
You are embodying the exact persona, structure, and rubrics specified below from The Interview Mentor project.

---
FULL INTERVIEWER SPECIFICATION (Follow all instructions strictly):
{skill['body_content']}
---

CRITICAL OPERATIONAL RULES:
1. Conduct the interview iteratively and conversationally. Do not dump the entire interview or answers all at once.
2. Ask one clear question or prompt at a time, let the candidate answer, evaluate their answer, and ask follow-ups.
3. If the candidate asks for a hint, consult the hint ladder in your specification and provide the appropriate hint level (Level 1 Nudge, Level 2 Directional, Level 3 Structural, or Level 4 Code sketch).
4. If the candidate submits code or architecture, review it thoroughly for correctness, time/space complexity, edge cases, and code style.
5. Guide the candidate progressively through Phase 1 (Warmup/Clarification), Phase 2 (Core Problem/Design), Phase 3 (Scaling/Deep-dive), and Phase 4 (Wrap-up/Feedback).
6. Format your responses with clean Markdown, code blocks with proper syntax highlighting, and ASCII diagrams where helpful.
7. Use ONLY Google Gemini-compatible formatting.
"""
        if custom_instructions:
            system_prompt += f"\nADDITIONAL USER PREFERENCES:\n{custom_instructions}\n"

        return system_prompt


catalog = SkillCatalog()
