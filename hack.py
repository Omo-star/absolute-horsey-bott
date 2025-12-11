from economy_shared import state, save_state
import discord
from discord.ext import commands
from discord import app_commands
from clang.cindex import Index, CursorKind
import ast
import random
import math
import datetime
import asyncio
import os
import re

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class HackerUniverse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.openrouter_client = None
        self.groq_client = None
        self.gemini_models = []
        self.clang_index = None
        self._init_ai_clients()
        self._init_clang()

    def _init_ai_clients(self):
        or_key = os.getenv("OPENROUTER_KEY")
        if OpenAI and or_key:
            try:
                self.openrouter_client = OpenAI(
                    api_key=or_key,
                    base_url="https://openrouter.ai/api/v1",
                    default_headers={
                        "HTTP-Referer": "https://example.com",
                        "X-Title": "Discord Hack RPG",
                    },
                )
            except Exception:
                self.openrouter_client = None
        groq_key = os.getenv("GROQ")
        if Groq and groq_key:
            try:
                self.groq_client = Groq(api_key=groq_key)
            except Exception:
                self.groq_client = None
        gemini_key = os.getenv("GEMINI_API_KEY")
        if genai and gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.gemini_models = ["gemini-2.5-flash", "gemini-2.0-flash"]
            except Exception:
                self.gemini_models = []

    def _init_clang(self):
        try:
            self.clang_index = Index.create()
        except Exception:
            self.clang_index = None

    def get_profile(self, user_id):
        uid = str(user_id)
        if "hacker_profiles" not in state:
            state["hacker_profiles"] = {}
        if uid not in state["hacker_profiles"]:
            state["hacker_profiles"][uid] = {
                "skill": 1,
                "xp": 0,
                "tier": 1,
                "trace": 0,
                "reputation": 0,
                "streak": 0,
                "last_hack": None,
                "specializations": [],
                "hack_history": [],
                "style_vector": {
                    "aggressive": 0.0,
                    "stealthy": 0.0,
                    "bruteforce": 0.0,
                    "elegant": 0.0,
                    "experimental": 0.0,
                },
            }
            save_state()
        return state["hacker_profiles"][uid]

    def get_user_pad(self, user_id):
        uid = str(user_id)
        if "codepad" not in state:
            state["codepad"] = {}
        if uid not in state["codepad"]:
            state["codepad"][uid] = {}
            save_state()
        return state["codepad"][uid]

    def analyze_script_ast(self, filename, code):
        try:
            tree = ast.parse(code)
        except Exception:
            return None
        fn_defs = []
        class_defs = 0
        loops = 0
        branches = 0
        comprehensions = 0
        calls = 0
        recursion = False
        max_depth = 0

        def visit(node, depth):
            nonlocal loops, branches, comprehensions, calls, recursion, max_depth, class_defs
            if depth > max_depth:
                max_depth = depth
            if isinstance(node, ast.FunctionDef):
                fn_defs.append(node.name)
            if isinstance(node, ast.ClassDef):
                class_defs += 1
            if isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
                loops += 1
            if isinstance(node, (ast.If, ast.Match)):
                branches += 1
            if isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                comprehensions += 1
            if isinstance(node, ast.Call):
                calls += 1
                if isinstance(node.func, ast.Name) and node.func.id in fn_defs:
                    recursion = True
            for child in ast.iter_child_nodes(node):
                visit(child, depth + 1)

        visit(tree, 0)
        code_len = len(code)
        lines = code.splitlines()
        non_empty = [l for l in lines if l.strip()]
        tokens = re.findall(r"\S+", code)
        line_count = len(lines)
        non_empty_count = len(non_empty)
        token_count = len(tokens)
        unique_tokens = len(set(tokens))
        density = token_count / line_count if line_count else 0.0
        branching_factor = branches + loops + comprehensions
        structural_complexity = branching_factor + max_depth + (3 if recursion else 0)
        size_penalty = max(0.0, (code_len - 2000) / 3000.0) if code_len > 2000 else 0.0
        efficiency = max(0.1, min(10.0, 4.2 + density * 0.35 - structural_complexity * 0.05 - size_penalty * 0.7))
        elegance = max(0.1, min(10.0, 3.0 + comprehensions * 0.7 + class_defs * 0.6 - loops * 0.25))
        aggression = max(0.1, min(10.0, 1.8 + loops * 0.6 + calls * 0.2))
        stealth = max(0.1, min(10.0, 5.5 + max_depth * 0.25 - branching_factor * 0.08))
        experimental = max(0.1, min(10.0, 2.2 + (unique_tokens / max(1, token_count)) * 18.0))
        return {
            "filename": filename,
            "line_count": line_count,
            "non_empty": non_empty_count,
            "token_count": token_count,
            "unique_tokens": unique_tokens,
            "fn_defs": len(fn_defs),
            "class_defs": class_defs,
            "loops": loops,
            "branches": branches,
            "comprehensions": comprehensions,
            "calls": calls,
            "recursion": recursion,
            "max_depth": max_depth,
            "efficiency": efficiency,
            "elegance": elegance,
            "aggression": aggression,
            "stealth": stealth,
            "experimental": experimental,
        }

    def analyze_cpp_libclang(self, filename, code, language):
        if not self.clang_index:
            try:
                self.clang_index = Index.create()
            except Exception:
                return None
        import tempfile
        suffix = ""
        lower = filename.lower()
        if lower.endswith(".cpp") or lower.endswith(".cxx") or lower.endswith(".cc"):
            suffix = ".cpp"
        elif lower.endswith(".hpp"):
            suffix = ".hpp"
        elif lower.endswith(".h"):
            suffix = ".h"
        else:
            suffix = ".c"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(code.encode("utf-8"))
            tmp_path = tmp.name
        args = []
        if language == "cpp":
            args = ["-std=c++17"]
        else:
            args = ["-std=c11"]
        try:
            tu = self.clang_index.parse(tmp_path, args=args)
        except Exception:
            return None
        loops = 0
        branches = 0
        fn_defs = 0
        class_defs = 0
        calls = 0
        max_depth = 0
        template_nodes = 0

        def visit(node, depth=0):
            nonlocal loops, branches, fn_defs, class_defs, calls, max_depth, template_nodes
            max_depth = max(max_depth, depth)
            k = node.kind
            if k in (CursorKind.FUNCTION_DECL, CursorKind.CXX_METHOD, CursorKind.CONSTRUCTOR, CursorKind.DESTRUCTOR):
                fn_defs += 1
            if k in (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL, CursorKind.CLASS_TEMPLATE):
                class_defs += 1
            if k in (CursorKind.FOR_STMT, CursorKind.WHILE_STMT, CursorKind.DO_STMT, CursorKind.CXX_FOR_RANGE_STMT):
                loops += 1
            if k in (CursorKind.IF_STMT, CursorKind.SWITCH_STMT, CursorKind.CASE_STMT, CursorKind.DEFAULT_STMT, CursorKind.CONDITIONAL_OPERATOR):
                branches += 1
            if k in (CursorKind.CALL_EXPR, CursorKind.CXX_MEMBER_CALL_EXPR):
                calls += 1
            if k in (CursorKind.CLASS_TEMPLATE, CursorKind.FUNCTION_TEMPLATE, CursorKind.TYPE_REF, CursorKind.TEMPLATE_REF):
                template_nodes += 1
            for child in node.get_children():
                visit(child, depth + 1)

        visit(tu.cursor, 0)
        lines = code.splitlines()
        line_count = len(lines)
        non_empty = [l for l in lines if l.strip()]
        non_empty_count = len(non_empty)
        tokens = re.findall(r"\S+", code)
        token_count = len(tokens)
        unique_tokens = len(set(tokens))
        pointer_ops = code.count("*")
        ref_ops = code.count("&")
        density = token_count / line_count if line_count else 0.0
        branching_factor = branches + loops
        raw_complex = branching_factor + max_depth + fn_defs * 0.3 + class_defs * 0.4
        pointer_intensity = (pointer_ops + ref_ops) / max(1, line_count)
        template_intensity = template_nodes / max(1, fn_defs + class_defs + 1)
        efficiency = max(0.1, min(10.0, 4.0 + density * 0.25 - raw_complex * 0.03))
        elegance = max(0.1, min(10.0, 2.8 + class_defs * 0.6 + template_intensity * 4.0 - loops * 0.2))
        aggression = max(0.1, min(10.0, 2.5 + loops * 0.6 + calls * 0.2 + pointer_intensity * 3.0))
        stealth = max(0.1, min(10.0, 4.5 + max_depth * -0.05 - branching_factor * 0.05 + template_intensity * 2.0))
        experimental = max(0.1, min(10.0, 1.5 + unique_tokens / max(1, token_count) * 10.0 + template_intensity * 5.0))
        return {
            "filename": filename,
            "line_count": line_count,
            "non_empty": non_empty_count,
            "token_count": token_count,
            "unique_tokens": unique_tokens,
            "fn_defs": fn_defs,
            "class_defs": class_defs,
            "loops": loops,
            "branches": branches,
            "comprehensions": 0,
            "calls": calls,
            "recursion": False,
            "max_depth": max_depth,
            "efficiency": efficiency,
            "elegance": elegance,
            "aggression": aggression,
            "stealth": stealth,
            "experimental": experimental,
        }

    def infer_archetype(self, filename, stats, code):
        name = filename.lower()
        if any(k in name for k in ["recon", "scan", "probe", "map", "survey"]):
            return "recon"
        if any(k in name for k in ["auth", "login", "access", "breakin", "door"]):
            return "access"
        if any(k in name for k in ["payload", "inject", "exploit", "shell", "bomb"]):
            return "payload"
        if any(k in name for k in ["exfil", "extract", "leak", "proxy", "tunnel", "drain"]):
            return "extraction"
        if any(k in name for k in ["core", "util", "common", "shared", "base"]):
            return "support"
        text = code.lower()
        if "socket" in text or "request" in text or "http" in text:
            return "recon"
        if "encrypt" in text or "decrypt" in text or "hash" in text or "sha" in text or "aes" in text:
            return "access"
        if "compress" in text or "encode" in text or "payload" in text or "packet" in text:
            return "payload"
        if "proxy" in text or "route" in text or "vpn" in text or "exfil" in text or "upload" in text:
            return "extraction"
        return "generic"

    def script_language(self, filename, code):
        lower = filename.lower()
        if lower.endswith(".py"):
            return "python"
        if lower.endswith(".cpp") or lower.endswith(".cxx") or lower.endswith(".cc") or lower.endswith(".hpp"):
            return "cpp"
        if lower.endswith(".c") or lower.endswith(".h"):
            if "class " in code or "template<" in code or "std::" in code:
                return "cpp"
            return "c"
        return "python"

    def rarity_from_stats(self, stats):
        score = stats["efficiency"] + stats["elegance"] + stats["stealth"] + stats["experimental"] + stats["aggression"]
        if score >= 40:
            return "mythic"
        if score >= 32:
            return "legendary"
        if score >= 25:
            return "epic"
        if score >= 18:
            return "rare"
        return "common"

    def analyze_all_scripts(self, pad):
        analyses = {}
        for fn, code in pad.items():
            if not isinstance(code, str) or not code.strip():
                continue
            lang = self.script_language(fn, code)
            if lang in ("c", "cpp"):
                ast_stats = self.analyze_cpp_libclang(fn, code, lang)
            else:
                ast_stats = self.analyze_script_ast(fn, code)
            if not ast_stats:
                continue
            archetype = self.infer_archetype(fn, ast_stats, code)
            rarity = self.rarity_from_stats(ast_stats)
            analyses[fn] = {
                "filename": fn,
                "language": lang,
                "archetype": archetype,
                "rarity": rarity,
                "ast": ast_stats,
            }
        return analyses

    def select_modules(self, analyses, recon_name, access_name, payload_name, extract_name):
        def pick(name, role):
            if name and name in analyses:
                return analyses[name]
            candidates = [a for a in analyses.values() if a["archetype"] == role]
            if not candidates:
                candidates = list(analyses.values())
            if not candidates:
                return None
            candidates.sort(key=lambda a: a["ast"]["efficiency"] + a["ast"]["elegance"] + a["ast"]["stealth"] + a["ast"]["experimental"], reverse=True)
            return candidates[0]
        recon = pick(recon_name, "recon")
        access = pick(access_name, "access")
        payload = pick(payload_name, "payload")
        extraction = pick(extract_file, "extraction") if False else pick(extract_name, "extraction")
        return {
            "recon": recon,
            "access": access,
            "payload": payload,
            "extraction": extraction,
        }

    def get_target_space(self):
        if "hack_targets" not in state:
            state["hack_targets"] = {}
            save_state()
        return state["hack_targets"]

    def get_or_create_target(self, target_id, difficulty):
        space = self.get_target_space()
        key = f"{target_id}:{difficulty}"
        if key in space:
            return space[key]
        base_security = 25 + difficulty * 20
        anomaly = 15 + difficulty * 15
        bandwidth = 20 + difficulty * 10
        forensics = 15 + difficulty * 18
        temperament = random.choice(["paranoid", "adaptive", "lazy", "spiky", "bursty", "evasive"])
        style_bias = {
            "aggressive": random.uniform(-0.2, 0.4),
            "stealthy": random.uniform(0.0, 0.5),
            "bruteforce": random.uniform(-0.3, 0.3),
            "elegant": random.uniform(0.0, 0.4),
            "experimental": random.uniform(-0.2, 0.4),
        }
        profile = {
            "id": key,
            "name": target_id,
            "difficulty": difficulty,
            "security_integrity": base_security,
            "anomaly_detection": anomaly,
            "bandwidth_pressure": bandwidth,
            "forensic_risk": forensics,
            "temperament": temperament,
            "style_bias": style_bias,
            "battles": 0,
            "wins": 0,
            "losses": 0,
        }
        space[key] = profile
        save_state()
        return profile

    async def generate_target_lore(self, target_profile):
        name = target_profile["name"]
        difficulty = target_profile["difficulty"]
        temperament = target_profile["temperament"]
        text = f"The {name} node is a difficulty {difficulty} defense surface behaving like a {temperament} network intelligence."
        if not self.openrouter_client and not self.groq_client and not self.gemini_models:
            return text
        system = "You generate extremely short flavor blurbs about fictional network targets, 1-2 sentences, no markdown."
        user = f"Describe the target system named {name} with temperament {temperament} in 1-2 vivid but concise sentences."
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        try:
            if self.openrouter_client:
                resp = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.openrouter_client.chat.completions.create(
                        model="meta-llama/llama-3.1-70b-instruct",
                        messages=messages,
                        max_tokens=80,
                        temperature=0.9,
                    ),
                )
                txt = resp.choices[0].message.content.strip()
                if txt:
                    return txt
        except Exception:
            pass
        try:
            if self.groq_client:
                resp = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.groq_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=messages,
                        max_tokens=80,
                        temperature=0.9,
                    ),
                )
                txt = resp.choices[0].message.content.strip()
                if txt:
                    return txt
        except Exception:
            pass
        try:
            if self.gemini_models:
                model = genai.GenerativeModel(self.gemini_models[0])
                resp = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: model.generate_content(user),
                )
                if hasattr(resp, "text") and resp.text:
                    return resp.text.strip()
        except Exception:
            pass
        return text

    def update_style_vector(self, profile, analyses):
        v = profile.get("style_vector", {})
        if not v:
            v = {
                "aggressive": 0.0,
                "stealthy": 0.0,
                "bruteforce": 0.0,
                "elegant": 0.0,
                "experimental": 0.0,
            }
        total = {
            "aggressive": 0.0,
            "stealthy": 0.0,
            "bruteforce": 0.0,
            "elegant": 0.0,
            "experimental": 0.0,
        }
        count = 0
        for mod in analyses.values():
            a = mod["ast"]
            total["aggressive"] += a["aggression"]
            total["stealthy"] += a["stealth"]
            total["bruteforce"] += a["loops"] + a["branches"]
            total["elegant"] += a["elegance"]
            total["experimental"] += a["experimental"]
            count += 1
        if count == 0:
            profile["style_vector"] = v
            return profile
        for k in total:
            avg = total[k] / count
            v[k] = v.get(k, 0.0) * 0.7 + avg * 0.3
        profile["style_vector"] = v
        return profile

    def difficulty_profile(self, target_profile, style_vector):
        s = target_profile
        base_security = s["security_integrity"]
        anomaly = s["anomaly_detection"]
        bandwidth = s["bandwidth_pressure"]
        forensic = s["forensic_risk"]
        bias = s["style_bias"]
        ag = style_vector.get("aggressive", 0.0)
        st = style_vector.get("stealthy", 0.0)
        br = style_vector.get("bruteforce", 0.0)
        el = style_vector.get("elegant", 0.0)
        ex = style_vector.get("experimental", 0.0)
        scale = 0.05
        base_security *= 1.0 + (bias["aggressive"] * scale * ag - bias["elegant"] * scale * el)
        anomaly *= 1.0 + (bias["experimental"] * scale * ex - bias["stealthy"] * scale * st)
        bandwidth *= 1.0 + (bias["bruteforce"] * scale * br)
        forensic *= 1.0 + (bias["stealthy"] * scale * st - bias["aggressive"] * scale * ag)
        return {
            "security_integrity": base_security,
            "anomaly_detection": anomaly,
            "bandwidth_pressure": bandwidth,
            "forensic_risk": forensic,
        }

    def compute_profile_modifiers(self, profile):
        skill = profile.get("skill", 1)
        tier = profile.get("tier", 1)
        trace = profile.get("trace", 0)
        rep = profile.get("reputation", 0)
        streak = profile.get("streak", 0)
        base = 1.0 + min(1.5, (skill - 1) * 0.03 + (tier - 1) * 0.08 + rep * 0.02)
        streak_bonus = 1.0 + min(0.5, streak * 0.05)
        trace_penalty = 1.0 + min(0.9, trace * 0.05)
        return {
            "global": base * streak_bonus,
            "trace_penalty": trace_penalty,
            "recon": 1.0 + min(0.6, (skill + tier) * 0.02),
            "access": 1.0 + min(0.7, (skill + tier) * 0.025),
            "payload": 1.0 + min(0.7, (skill + tier) * 0.025),
            "extraction": 1.0 + min(0.6, (skill + tier) * 0.02),
        }

    def compute_phase_score(self, phase, module, profile_mod, diff_profile, profile, target_profile):
        if not module:
            base_power = 8.0
            script_factor = 2.0
            lang = "none"
        else:
            a = module["ast"]
            lang = module.get("language", "python")
            if phase == "recon":
                base_power = a["efficiency"] * 1.2 + a["stealth"] * 1.4 + a["experimental"] * 0.8
                script_factor = a["elegance"] + a["loops"] * 0.4
            elif phase == "access":
                base_power = a["efficiency"] * 1.5 + a["aggression"] * 1.1 + a["branches"] * 0.7
                script_factor = a["calls"] * 0.4 + a["max_depth"] * 0.5
            elif phase == "payload":
                base_power = a["elegance"] * 1.4 + a["experimental"] * 1.1 + a["efficiency"]
                script_factor = a["comprehensions"] * 0.8 + a["class_defs"] * 0.6
            else:
                base_power = a["stealth"] * 1.6 + a["efficiency"] + a["experimental"] * 0.6
                script_factor = a["max_depth"] * 0.4 + a["fn_defs"] * 0.3
        if lang == "python":
            base_power *= 1.05
            if phase in ("recon", "extraction"):
                script_factor *= 1.1
        elif lang == "c":
            base_power *= 1.1 if phase in ("access", "payload") else base_power * 1.0
            script_factor *= 1.05
        elif lang == "cpp":
            base_power *= 1.08
            script_factor *= 1.08
        temperament = target_profile["temperament"]
        if temperament == "paranoid" and phase in ("recon", "access"):
            base_power *= 0.9
        if temperament == "lazy" and phase == "recon":
            base_power *= 1.1
        if temperament == "bursty" and phase == "payload":
            base_power *= 1.05
        if temperament == "evasive" and phase == "extraction":
            base_power *= 0.9
        if phase == "recon":
            th = diff_profile["security_integrity"] * 0.75 + diff_profile["anomaly_detection"] * 0.5
            bonus = profile_mod["recon"]
        elif phase == "access":
            th = diff_profile["security_integrity"] * 1.25 + diff_profile["anomaly_detection"] * 0.7
            bonus = profile_mod["access"]
        elif phase == "payload":
            th = diff_profile["bandwidth_pressure"] * 1.0 + diff_profile["security_integrity"] * 0.8
            bonus = profile_mod["payload"]
        else:
            th = diff_profile["forensic_risk"] * 1.0 + diff_profile["anomaly_detection"] * 0.8
            bonus = profile_mod["extraction"]
        th *= profile_mod["trace_penalty"]
        power = (base_power * profile_mod["global"] * bonus) + script_factor * 1.1
        margin = power - th
        success = margin >= 0.0
        closeness = abs(margin) / max(1.0, th)
        rng_window = max(0.0, 0.18 - closeness)
        flipped = False
        if rng_window > 0:
            roll = random.random()
            if margin < 0 and roll < rng_window * 0.55:
                success = True
                flipped = True
            elif margin > 0 and roll < rng_window * 0.3:
                success = False
                flipped = True
        if success:
            if margin > th * 0.3:
                quality = "flawless"
            elif margin < th * 0.05:
                quality = "barely"
            else:
                quality = "clean"
        else:
            if margin > -th * 0.1:
                quality = "almost"
            else:
                quality = "failed"
        return {
            "phase": phase,
            "module": module,
            "power": power,
            "threshold": th,
            "margin": margin,
            "success": success,
            "flipped": flipped,
            "quality": quality,
        }

    def aggregate_outcome(self, phase_results):
        successes = [p for p in phase_results if p["success"]]
        fails = [p for p in phase_results if not p["success"]]
        flawless = sum(1 for p in phase_results if p["quality"] == "flawless"]
        barely = sum(1 for p in phase_results if p["quality"] == "barely"]
        almost = sum(1 for p in phase_results if p["quality"] == "almost"]
        fail_count = len(fails)
        success = len(successes) >= 3 or (len(successes) >= 2 and flawless >= 1)
        if success:
            if flawless >= 2 and fail_count == 0:
                quality = "perfect_chain"
            elif flawless >= 1 and barely == 0 and fail_count == 0:
                quality = "strong"
            elif barely >= 1:
                quality = "shaky"
            else:
                quality = "clean"
        else:
            if almost >= 2:
                quality = "near_miss"
            elif fail_count == 4:
                quality = "catastrophic"
            else:
                quality = "messy"
        archetypes = [p["module"]["archetype"] for p in phase_results if p["module"]]
        languages = [p["module"]["language"] for p in phase_results if p["module"] and "language" in p["module"]]
        synergy = 0.0
        if archetypes:
            if len(set(archetypes)) == 1:
                synergy += 0.15
            if len(set(archetypes)) >= 3:
                synergy += 0.15
        if languages:
            if len(set(languages)) >= 3:
                synergy += 0.1
            if len(set(languages)) == 1:
                synergy += 0.05
        return {
            "success": success,
            "quality": quality,
            "synergy": synergy,
            "flawless": flawless,
            "fails": fail_count,
        }

    def apply_progression(self, profile, difficulty, outcome, phase_results, target_profile):
        base_xp = 12 * difficulty
        if outcome["quality"] == "perfect_chain":
            base_xp *= 2.4
        elif outcome["quality"] == "strong":
            base_xp *= 1.8
        elif outcome["quality"] == "clean":
            base_xp *= 1.4
        elif outcome["quality"] == "shaky":
            base_xp *= 1.1
        elif outcome["quality"] == "near_miss":
            base_xp *= 0.8
        elif outcome["quality"] == "messy":
            base_xp *= 0.5
        else:
            base_xp *= 0.3
        xp_gain = int(base_xp)
        skill_delta = 0
        rep_delta = 0
        trace_delta = 0
        if outcome["success"]:
            skill_delta += 1 + difficulty // 2
            rep_delta += 1 + difficulty
            trace_delta -= 1
            for p in phase_results:
                if p["success"] and p["quality"] == "flawless":
                    skill_delta += 1
                    rep_delta += 1
        else:
            trace_delta += 1 + difficulty
            if profile.get("skill", 1) > 3:
                skill_delta -= 1
            rep_delta -= 1
        profile["xp"] = profile.get("xp", 0) + xp_gain
        profile["skill"] = max(1, profile.get("skill", 1) + skill_delta)
        profile["reputation"] = max(0, profile.get("reputation", 0) + rep_delta)
        profile["trace"] = max(0, min(40, profile.get("trace", 0) + trace_delta))
        profile["streak"] = profile.get("streak", 0) + 1 if outcome["success"] else 0
        while profile["xp"] >= 120 * profile.get("tier", 1):
            profile["xp"] -= 120 * profile.get("tier", 1)
            profile["tier"] += 1
        tspace = self.get_target_space()
        tid = target_profile["id"]
        if tid in tspace:
            t = tspace[tid]
            t["battles"] += 1
            if outcome["success"]:
                t["losses"] += 1
                t["security_integrity"] *= 1.03
                t["anomaly_detection"] *= 1.04
                t["forensic_risk"] *= 1.02
            else:
                t["wins"] += 1
                t["security_integrity"] *= 1.01
                t["bandwidth_pressure"] *= 1.02
            tspace[tid] = t
        save_state()
        return {
            "xp_gain": xp_gain,
            "skill_delta": skill_delta,
            "rep_delta": rep_delta,
            "trace_delta": trace_delta,
        }

    def compute_cooldown(self, profile, difficulty):
        base = 45 + difficulty * 25
        base += profile.get("trace", 0) * 3
        base -= profile.get("skill", 1) * 1.5
        base -= profile.get("tier", 1) * 3
        base = max(20, min(900, int(base)))
        return base

    def format_module_summary(self, modules):
        parts = []
        for key in ["recon", "access", "payload", "extraction"]:
            mod = modules.get(key)
            if not mod:
                parts.append(f"{key.title()}: none")
                continue
            a = mod["ast"]
            lang = mod.get("language", "python")
            rarity = mod.get("rarity", "common")
            seg = f"{key.title()}: `{mod['filename']}` [{lang}/{rarity}] | eff {a['efficiency']:.1f}, stealth {a['stealth']:.1f}, aggr {a['aggression']:.1f}, eleg {a['elegance']:.1f}"
            parts.append(seg)
        return "\n".join(parts) if parts else "No modules."

    def format_profile_status(self, profile):
        sv = profile.get("style_vector", {})
        lines = []
        lines.append(f"Skill: **{profile.get('skill', 1)}**  Tier: **{profile.get('tier', 1)}**  XP: **{profile.get('xp', 0)}**")
        lines.append(f"Trace: **{profile.get('trace', 0)} / 40**  Reputation: **{profile.get('reputation', 0)}**  Streak: **{profile.get('streak', 0)}**")
        if sv:
            lines.append(f"Style → Aggressive {sv.get('aggressive', 0.0):.1f}, Stealthy {sv.get('stealthy', 0.0):.1f}, Bruteforce {sv.get('bruteforce', 0.0):.1f}, Elegant {sv.get('elegant', 0.0):.1f}, Experimental {sv.get('experimental', 0.0):.1f}")
        return "\n".join(lines)

    def format_target_status(self, target_profile):
        t = target_profile
        lines = []
        lines.append(f"Security integrity: **{t['security_integrity']:.1f}**")
        lines.append(f"Anomaly detection: **{t['anomaly_detection']:.1f}**")
        lines.append(f"Bandwidth pressure: **{t['bandwidth_pressure']:.1f}**")
        lines.append(f"Forensic risk: **{t['forensic_risk']:.1f}**")
        lines.append(f"Temperament: **{t['temperament']}**")
        lines.append(f"Record: **{t['wins']}W / {t['losses']}L** over {t['battles']} intrusions")
        return "\n".join(lines)

    async def animate_chain(self, message, target, modules, difficulty, target_profile):
        phases = [
            ("recon", "Reconnaissance", "📡", ["Mapping endpoints", "Fingerprinting defenses", "Sampling telemetry", "Building topology graph"]),
            ("access", "Access Vector", "🧬", ["Normalizing credential space", "Aligning solver heuristics", "Injecting probes", "Deforming auth surface"]),
            ("payload", "Payload Orchestration", "💾", ["Assembling segments", "Packing and encrypting", "Scrambling signatures", "Priming execution hooks"]),
            ("extraction", "Exfiltration", "🚀", ["Splicing data streams", "Braiding proxies", "Masking envelopes", "Evacuating ghost channels"]),
        ]
        for key, label, icon, steps in phases:
            for i in range(len(steps)):
                rows = []
                for idx, step in enumerate(steps):
                    if idx < i:
                        prefix = "✅"
                    elif idx == i:
                        prefix = "🟡"
                    else:
                        prefix = "⚪"
                    rows.append(f"{prefix} {step}")
                module = modules.get(key)
                mod_name = module["filename"] if module else "no module"
                embed = discord.Embed(
                    title=f"{icon} {label} → {target}",
                    description="\n".join(rows),
                    color=discord.Color.blurple(),
                )
                embed.add_field(name="Active module", value=f"`{mod_name}`", inline=False)
                embed.add_field(name="Difficulty", value=str(difficulty), inline=True)
                embed.add_field(name="Temperament", value=target_profile["temperament"], inline=True)
                await message.edit(embed=embed)
                await asyncio.sleep(0.6)

    def build_final_embed(self, user, target, modules, profile, difficulty, target_profile, phase_results, outcome, progression, lore):
        success = outcome["success"]
        if success:
            title = f"✅ Breach Complete: {target}"
            color = discord.Color.green()
        else:
            title = f"❌ Intrusion Disrupted: {target}"
            color = discord.Color.red()
        name_map = {
            "recon": "Reconnaissance",
            "access": "Access",
            "payload": "Payload",
            "extraction": "Extraction",
        }
        lines = []
        for res in phase_results:
            label = name_map.get(res["phase"], res["phase"].title())
            symbol = "✅" if res["success"] else "❌"
            if res["quality"] == "flawless":
                symbol = "💎"
            elif res["quality"] in ("barely", "almost"):
                symbol = "⚠️"
            module_name = res["module"]["filename"] if res["module"] else "no module"
            margin_pct = res["margin"] / max(1.0, res["threshold"])
            margin_pct = max(-1.0, min(1.0, margin_pct))
            lines.append(f"{symbol} {label} | `{module_name}` | power {res['power']:.1f} vs {res['threshold']:.1f} ({margin_pct*100:.1f}%) → {res['quality']}")
        desc = "\n".join(lines) if lines else "No phases evaluated."
        embed = discord.Embed(title=title, description=desc, color=color)
        out_lines = []
        if success:
            if outcome["quality"] == "perfect_chain":
                out_lines.append("Chain rating: **perfect execution**")
            elif outcome["quality"] == "strong":
                out_lines.append("Chain rating: **strong compromise**")
            elif outcome["quality"] == "clean":
                out_lines.append("Chain rating: **clean breach**")
            elif outcome["quality"] == "shaky":
                out_lines.append("Chain rating: **shaky but successful**")
            else:
                out_lines.append(f"Chain rating: **{outcome['quality']}**")
        else:
            if outcome["quality"] == "near_miss":
                out_lines.append("Chain rating: **near miss**")
            elif outcome["quality"] == "catastrophic":
                out_lines.append("Chain rating: **catastrophic failure**")
            else:
                out_lines.append(f"Chain rating: **{outcome['quality']}**")
        out_lines.append(f"XP: **+{progression['xp_gain']}**")
        sd = progression["skill_delta"]
        rd = progression["rep_delta"]
        td = progression["trace_delta"]
        out_lines.append(f"Skill: **{sd:+d}**")
        out_lines.append(f"Reputation: **{rd:+d}**")
        out_lines.append(f"Trace: **{td:+d}**")
        if outcome["synergy"] != 0.0:
            out_lines.append(f"Module synergy bonus: **{int(outcome['synergy']*100)}%** cohesion")
        embed.add_field(name="Outcome", value="\n".join(out_lines), inline=False)
        embed.add_field(name="Modules", value=self.format_module_summary(modules), inline=False)
        embed.add_field(name="Hacker status", value=self.format_profile_status(profile), inline=False)
        embed.add_field(name="Target profile", value=self.format_target_status(target_profile), inline=False)
        if lore:
            embed.add_field(name="Target lore", value=lore, inline=False)
        embed.set_footer(text=f"Hacker ID {user.id} • Difficulty {difficulty}")
        return embed

    @app_commands.command(name="hack", description="Execute a multi-phase code-based hacking run against an evolving AI target.")
    @app_commands.describe(
        target="Target system name or identifier",
        difficulty="1=trivial, 5=insane",
        recon_file="Optional recon script filename from your codepad",
        access_file="Optional access script filename from your codepad",
        payload_file="Optional payload script filename from your codepad",
        extract_file="Optional extraction script filename from your codepad",
    )
    async def hack(
        self,
        interaction: discord.Interaction,
        target: str,
        difficulty: int = 2,
        recon_file: str | None = None,
        access_file: str | None = None,
        payload_file: str | None = None,
        extract_file: str | None = None,
    ):
        user = interaction.user
        profile = self.get_profile(user.id)
        difficulty = max(1, min(5, difficulty))
        now = datetime.datetime.utcnow()
        last_raw = profile.get("last_hack")
        cd = self.compute_cooldown(profile, difficulty)
        if last_raw:
            try:
                last = datetime.datetime.fromisoformat(last_raw)
            except Exception:
                last = None
            if last is not None:
                delta = (now - last).total_seconds()
                remaining = cd - delta
                if remaining > 0:
                    await interaction.response.send_message(f"⏳ Rigs recalibrating, try again in **{int(remaining)}s**.", ephemeral=True)
                    return
        pad = self.get_user_pad(user.id)
        analyses = self.analyze_all_scripts(pad)
        if not analyses:
            await interaction.response.send_message("❌ No usable scripts found in your codepad. Create scripts with `/code_new` and `/code_edit` first.", ephemeral=True)
            return
        profile = self.update_style_vector(profile, analyses)
        target_profile = self.get_or_create_target(target, difficulty)
        diff_profile = self.difficulty_profile(target_profile, profile.get("style_vector", {}))
        modules = self.select_modules(analyses, recon_file, access_file, payload_file, extract_file)
        profile["last_hack"] = now.isoformat()
        save_state()
        await interaction.response.defer()
        lore = await self.generate_target_lore(target_profile)
        intro = discord.Embed(
            title=f"Initializing intrusion plan → {target}",
            description="Assembling phase chain from your code modules.",
            color=discord.Color.blurple(),
        )
        intro.add_field(name="Hacker status", value=self.format_profile_status(profile), inline=False)
        intro.add_field(name="Modules", value=self.format_module_summary(modules), inline=False)
        intro.add_field(name="Target profile", value=self.format_target_status(target_profile), inline=False)
        if lore:
            intro.add_field(name="Target lore", value=lore, inline=False)
        msg = await interaction.followup.send(embed=intro)
        await self.animate_chain(msg, target, modules, difficulty, target_profile)
        profile_mod = self.compute_profile_modifiers(profile)
        recon_res = self.compute_phase_score("recon", modules.get("recon"), profile_mod, diff_profile, profile, target_profile)
        access_res = self.compute_phase_score("access", modules.get("access"), profile_mod, diff_profile, profile, target_profile)
        payload_res = self.compute_phase_score("payload", modules.get("payload"), profile_mod, diff_profile, profile, target_profile)
        extract_res = self.compute_phase_score("extraction", modules.get("extraction"), profile_mod, diff_profile, profile, target_profile)
        phases = [recon_res, access_res, payload_res, extract_res]
        outcome = self.aggregate_outcome(phases)
        progression = self.apply_progression(profile, difficulty, outcome, phases, target_profile)
        if "hack_history" not in profile:
            profile["hack_history"] = []
        profile["hack_history"].append(
            {
                "target": target,
                "difficulty": difficulty,
                "success": outcome["success"],
                "quality": outcome["quality"],
                "timestamp": now.isoformat(),
            }
        )
        profile["hack_history"] = profile["hack_history"][-30:]
        save_state()
        final_embed = self.build_final_embed(user, target, modules, profile, difficulty, target_profile, phases, outcome, progression, lore)
        await msg.edit(embed=final_embed)

    @app_commands.command(name="hack_profile", description="View your hacking profile, style vector, and recent runs.")
    async def hack_profile(self, interaction: discord.Interaction):
        profile = self.get_profile(interaction.user.id)
        hist = profile.get("hack_history", [])
        lines = []
        for h in hist[-10:]:
            stamp = h.get("timestamp", "")[:19]
            ok = "✅" if h.get("success") else "❌"
            lines.append(f"{ok} {h.get('target','?')} d={h.get('difficulty',0)} q={h.get('quality','?')} at {stamp}")
        history_text = "\n".join(lines) if lines else "No runs recorded yet."
        embed = discord.Embed(
            title=f"Hacker profile for {interaction.user.display_name}",
            description=self.format_profile_status(profile),
            color=discord.Color.teal(),
        )
        embed.add_field(name="Recent runs", value=history_text, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="hack_targets", description="List known AI defense targets and their evolution.")
    async def hack_targets(self, interaction: discord.Interaction):
        space = self.get_target_space()
        if not space:
            await interaction.response.send_message("No targets have been instantiated yet. Run `/hack` first.", ephemeral=True)
            return
        lines = []
        for t in list(space.values())[:20]:
            lines.append(f"• {t['name']} d={t['difficulty']} | {t['wins']}W/{t['losses']}L | sec {t['security_integrity']:.1f}, anom {t['anomaly_detection']:.1f}")
        text = "\n".join(lines)
        embed = discord.Embed(
            title="Known network entities",
            description=text,
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(HackerUniverse(bot))
