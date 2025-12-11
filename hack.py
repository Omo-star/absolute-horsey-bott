from economy_shared import state, save_state
import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import math
import datetime
import re
from typing import Optional, Dict, Any, List, Tuple


class HackerRPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_profile(self, user_id: int) -> Dict[str, Any]:
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
                "last_hack": None,
                "specializations": [],
                "hack_history": [],
                "streak": 0,
            }
            save_state()
        return state["hacker_profiles"][uid]

    def get_user_pad(self, user_id: int) -> Dict[str, str]:
        uid = str(user_id)
        if "codepad" not in state:
            state["codepad"] = {}
        if uid not in state["codepad"]:
            state["codepad"][uid] = {}
            save_state()
        return state["codepad"][uid]

    def analyze_script_text(self, filename: str, code: str) -> Dict[str, Any]:
        lines = code.splitlines()
        non_empty_lines = [ln for ln in lines if ln.strip()]
        length = len(lines)
        non_empty_length = len(non_empty_lines)
        char_count = len(code)
        token_count = len(re.findall(r"\S+", code))
        keywords = [
            "for", "while", "if", "elif", "else", "def", "class", "try",
            "except", "finally", "with", "lambda", "yield", "return",
            "import", "from", "async", "await", "and", "or", "not"
        ]
        keyword_freq = {}
        for kw in keywords:
            keyword_freq[kw] = len(re.findall(r"\b" + re.escape(kw) + r"\b", code))
        nesting_depth = 0
        max_nesting = 0
        for ln in non_empty_lines:
            stripped = ln.lstrip()
            indent = len(ln) - len(stripped)
            level = indent // 4
            if level > max_nesting:
                max_nesting = level
        function_defs = re.findall(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", code)
        recursion_detected = False
        for fn in function_defs:
            pattern = r"\b" + re.escape(fn) + r"\s*\("
            body = re.split(r"def\s+" + re.escape(fn) + r"\s*\(", code, maxsplit=1)
            if len(body) > 1:
                if re.search(pattern, body[1]):
                    recursion_detected = True
                    break
        uses_async = "async def" in code or "await " in code
        uses_random = "random." in code
        uses_math = "math." in code
        uses_itertools = "itertools." in code
        uses_statistics = "statistics." in code or "stats." in code
        branch_points = keyword_freq["if"] + keyword_freq["elif"] + keyword_freq["while"] + keyword_freq["for"]
        complexity_score = branch_points + max_nesting + (2 if recursion_detected else 0)
        import_count = keyword_freq["import"] + keyword_freq["from"]
        compressed_chars = len(set(code))
        entropy_score = min(1.0, (compressed_chars / max(1, char_count)) * 10.0)
        name_lower = filename.lower()
        archetype = "generic"
        if any(tag in name_lower for tag in ["recon", "scan", "probe"]):
            archetype = "recon"
        elif any(tag in name_lower for tag in ["access", "login", "auth", "breakin"]):
            archetype = "access"
        elif any(tag in name_lower for tag in ["payload", "inject", "exploit"]):
            archetype = "payload"
        elif any(tag in name_lower for tag in ["exfil", "extract", "leak", "proxy"]):
            archetype = "extraction"
        elif any(tag in name_lower for tag in ["global", "core", "util"]):
            archetype = "support"
        efficiency_base = 0.0
        if length > 0:
            density = token_count / length
            efficiency_base += min(3.0, density / 5.0)
        if complexity_score > 0:
            efficiency_base += min(4.0, 10.0 / (1.0 + complexity_score))
        if uses_math:
            efficiency_base += 0.5
        if uses_itertools:
            efficiency_base += 0.5
        if uses_statistics:
            efficiency_base += 0.5
        if recursion_detected and max_nesting > 2:
            efficiency_base -= 0.5
        efficiency = max(0.1, min(10.0, efficiency_base))
        stealth_score = 5.0
        if uses_random:
            stealth_score += 0.5
        if complexity_score > 6:
            stealth_score += 0.5
        if import_count > 3:
            stealth_score -= 0.5
        stealth_score = max(0.1, min(10.0, stealth_score))
        parallelism_score = 1.0
        if "thread" in code.lower() or "concurrent" in code.lower():
            parallelism_score += 2.0
        if uses_async:
            parallelism_score += 2.0
        if "pool" in code.lower():
            parallelism_score += 1.0
        parallelism_score = max(0.1, min(10.0, parallelism_score))
        stability_score = 10.0
        if "try:" in code:
            stability_score += 1.0
        if "except" in code:
            stability_score += 1.0
        if "finally" in code:
            stability_score += 0.5
        if "raise" in code:
            stability_score -= 1.0
        if "exit(" in code or "quit(" in code:
            stability_score -= 2.0
        stability_score = max(0.1, min(10.0, stability_score))
        size_penalty = 0.0
        if char_count > 2000:
            size_penalty = (char_count - 2000) / 2000.0
        performance_score = max(0.1, min(10.0, efficiency - size_penalty))
        return {
            "filename": filename,
            "archetype": archetype,
            "length": length,
            "non_empty_length": non_empty_length,
            "char_count": char_count,
            "token_count": token_count,
            "keyword_freq": keyword_freq,
            "max_nesting": max_nesting,
            "recursion": recursion_detected,
            "uses_async": uses_async,
            "uses_random": uses_random,
            "uses_math": uses_math,
            "uses_itertools": uses_itertools,
            "uses_statistics": uses_statistics,
            "complexity_score": complexity_score,
            "import_count": import_count,
            "entropy_score": entropy_score,
            "efficiency": efficiency,
            "stealth": stealth_score,
            "parallelism": parallelism_score,
            "stability": stability_score,
            "performance": performance_score,
        }

    def select_modules(
        self,
        pad: Dict[str, str],
        recon_name: Optional[str],
        access_name: Optional[str],
        payload_name: Optional[str],
        extract_name: Optional[str],
    ) -> Dict[str, Dict[str, Any]]:
        analyses: Dict[str, Dict[str, Any]] = {}
        for fn, code in pad.items():
            if not code.strip():
                continue
            analyses[fn] = self.analyze_script_text(fn, code)
        def pick_by_name(name: Optional[str], fallback_role: str) -> Optional[Dict[str, Any]]:
            if name and name in analyses:
                return analyses[name]
            candidates = [a for a in analyses.values() if a["archetype"] == fallback_role]
            if not candidates:
                candidates = list(analyses.values())
            if not candidates:
                return None
            candidates_sorted = sorted(candidates, key=lambda x: x["performance"] + x["efficiency"] + x["stability"], reverse=True)
            return candidates_sorted[0]
        recon = pick_by_name(recon_name, "recon")
        access = pick_by_name(access_name, "access")
        payload = pick_by_name(payload_name, "payload")
        extract = pick_by_name(extract_name, "extraction")
        return {
            "recon": recon,
            "access": access,
            "payload": payload,
            "extraction": extract,
            "all": analyses,
        }

    def compute_profile_modifiers(self, profile: Dict[str, Any]) -> Dict[str, float]:
        skill = profile.get("skill", 1)
        tier = profile.get("tier", 1)
        trace = profile.get("trace", 0)
        streak = profile.get("streak", 0)
        reputation = profile.get("reputation", 0)
        global_bonus = 1.0 + min(1.0, (skill - 1) * 0.03 + (tier - 1) * 0.08)
        trace_penalty = 1.0 + min(0.8, trace * 0.04)
        streak_bonus = 1.0 + min(0.5, streak * 0.05)
        reputation_bonus = 1.0 + min(0.4, reputation * 0.02)
        return {
            "global_bonus": global_bonus * streak_bonus * reputation_bonus,
            "trace_penalty": trace_penalty,
            "recon_bonus": 1.0 + min(0.5, (skill + tier) * 0.02),
            "access_bonus": 1.0 + min(0.6, (skill + tier) * 0.03),
            "payload_bonus": 1.0 + min(0.6, (skill + tier) * 0.03),
            "extraction_bonus": 1.0 + min(0.5, (skill + tier) * 0.02),
        }

    def difficulty_profile(self, difficulty: int) -> Dict[str, float]:
        d = max(1, min(5, difficulty))
        security_integrity = 20 + d * 15
        anomaly_detection = 10 + d * 10
        bandwidth_pressure = 10 + d * 8
        forensic_risk = 10 + d * 12
        return {
            "security_integrity": security_integrity,
            "anomaly_detection": anomaly_detection,
            "bandwidth_pressure": bandwidth_pressure,
            "forensic_risk": forensic_risk,
        }

    def compute_phase_score(
        self,
        phase: str,
        module: Optional[Dict[str, Any]],
        profile_mod: Dict[str, float],
        diff_profile: Dict[str, float],
        profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not module:
            base_power = 5.0
            script_factor = 0.5
        else:
            if phase == "recon":
                base_power = module["efficiency"] + module["stealth"] + module["entropy_score"] * 4.0
                script_factor = module["performance"]
            elif phase == "access":
                base_power = module["performance"] * 1.4 + module["complexity_score"] * 0.7
                if module["uses_math"]:
                    base_power += 1.0
                if module["uses_statistics"]:
                    base_power += 0.8
                script_factor = module["efficiency"] + module["parallelism"]
            elif phase == "payload":
                base_power = module["efficiency"] + module["entropy_score"] * 6.0 + module["complexity_score"]
                script_factor = module["performance"] + module["stability"]
            elif phase == "extraction":
                base_power = module["stealth"] * 2.0 + module["entropy_score"] * 3.0 + module["parallelism"]
                script_factor = module["performance"] + module["stability"]
            else:
                base_power = 5.0
                script_factor = 1.0
        global_bonus = profile_mod["global_bonus"]
        if phase == "recon":
            bonus = profile_mod["recon_bonus"]
            threshold = diff_profile["security_integrity"] * 0.8 + diff_profile["anomaly_detection"] * 0.4
        elif phase == "access":
            bonus = profile_mod["access_bonus"]
            threshold = diff_profile["security_integrity"] * 1.2 + diff_profile["anomaly_detection"] * 0.6
        elif phase == "payload":
            bonus = profile_mod["payload_bonus"]
            threshold = diff_profile["bandwidth_pressure"] * 0.9 + diff_profile["security_integrity"] * 0.7
        elif phase == "extraction":
            bonus = profile_mod["extraction_bonus"]
            threshold = diff_profile["forensic_risk"] * 0.9 + diff_profile["anomaly_detection"] * 0.7
        else:
            bonus = 1.0
            threshold = 25.0
        adjusted_threshold = threshold * profile_mod["trace_penalty"]
        power = (base_power * bonus * global_bonus) + script_factor * 1.2
        margin = power - adjusted_threshold
        deterministic_success = margin >= 0.0
        closeness = abs(margin) / max(1.0, adjusted_threshold)
        rng_window = max(0.0, 0.22 - closeness)
        flip = False
        if rng_window > 0.0:
            roll = random.random()
            if margin < 0.0 and roll < rng_window * 0.5:
                deterministic_success = True
                flip = True
            elif margin > 0.0 and roll < rng_window * 0.3:
                deterministic_success = False
                flip = True
        quality = "clean"
        if deterministic_success:
            if margin > adjusted_threshold * 0.3:
                quality = "flawless"
            elif margin < adjusted_threshold * 0.05:
                quality = "barely"
        else:
            if margin > -adjusted_threshold * 0.1:
                quality = "almost"
            else:
                quality = "failed"
        return {
            "phase": phase,
            "module": module,
            "power": power,
            "threshold": adjusted_threshold,
            "margin": margin,
            "success": deterministic_success,
            "flip": flip,
            "quality": quality,
        }

    def aggregate_outcome(self, phase_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        successes = [p for p in phase_results if p["success"]]
        fails = [p for p in phase_results if not p["success"]]
        flawless_count = sum(1 for p in phase_results if p["quality"] == "flawless")
        barely_count = sum(1 for p in phase_results if p["quality"] == "barely")
        almost_count = sum(1 for p in phase_results if p["quality"] == "almost")
        fail_count = len(fails)
        main_success = len(successes) >= 3 or (len(successes) >= 2 and flawless_count >= 1)
        quality = "catastrophic"
        if main_success:
            if flawless_count >= 2 and barely_count == 0:
                quality = "perfect_chain"
            elif flawless_count >= 1 and fail_count == 0:
                quality = "strong"
            elif barely_count >= 1:
                quality = "shaky"
            else:
                quality = "clean"
        else:
            if almost_count >= 2:
                quality = "near_miss"
            elif fail_count == 4:
                quality = "catastrophic"
            else:
                quality = "messy"
        synergy_bonus = 0.0
        archetypes = [p["module"]["archetype"] for p in phase_results if p["module"]]
        if len(set(archetypes)) == 1 and archetypes:
            synergy_bonus += 0.1
        diversity = len(set(archetypes))
        if diversity >= 3:
            synergy_bonus += 0.15
        return {
            "success": main_success,
            "quality": quality,
            "synergy_bonus": synergy_bonus,
            "flawless_count": flawless_count,
            "fails": fail_count,
        }

    def apply_progression(
        self,
        profile: Dict[str, Any],
        difficulty: int,
        outcome: Dict[str, Any],
        phase_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        base_xp = 10 * difficulty
        if outcome["quality"] == "perfect_chain":
            base_xp *= 2.2
        elif outcome["quality"] == "strong":
            base_xp *= 1.7
        elif outcome["quality"] == "clean":
            base_xp *= 1.4
        elif outcome["quality"] == "shaky":
            base_xp *= 1.1
        elif outcome["quality"] == "near_miss":
            base_xp *= 0.7
        elif outcome["quality"] == "messy":
            base_xp *= 0.5
        elif outcome["quality"] == "catastrophic":
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
            skill_delta -= 1 if profile.get("skill", 1) > 3 else 0
            rep_delta -= 1
        profile["xp"] = profile.get("xp", 0) + xp_gain
        profile["skill"] = max(1, profile.get("skill", 1) + skill_delta)
        profile["reputation"] = max(0, profile.get("reputation", 0) + rep_delta)
        profile["trace"] = max(0, min(30, profile.get("trace", 0) + trace_delta))
        profile["streak"] = profile.get("streak", 0) + 1 if outcome["success"] else 0
        while profile["xp"] >= 100 * profile.get("tier", 1):
            profile["xp"] -= 100 * profile.get("tier", 1)
            profile["tier"] += 1
        return {
            "xp_gain": xp_gain,
            "skill_delta": skill_delta,
            "rep_delta": rep_delta,
            "trace_delta": trace_delta,
        }

    def compute_cooldown(self, profile: Dict[str, Any], difficulty: int) -> int:
        base = 40 + difficulty * 20
        base += profile.get("trace", 0) * 3
        base -= profile.get("skill", 1) * 2
        base -= profile.get("tier", 1) * 3
        base = max(15, min(600, base))
        return int(base)

    def format_module_summary(self, modules: Dict[str, Dict[str, Any]]) -> str:
        parts = []
        for key in ["recon", "access", "payload", "extraction"]:
            mod = modules.get(key)
            if not mod:
                parts.append(f"{key.title()}: None")
                continue
            stats = mod
            seg = f"{key.title()}: `{stats['filename']}` | perf {stats['performance']:.1f}, eff {stats['efficiency']:.1f}, stealth {stats['stealth']:.1f}, par {stats['parallelism']:.1f}"
            parts.append(seg)
        return "\n".join(parts) if parts else "No modules selected."

    def format_profile_status(self, profile: Dict[str, Any]) -> str:
        lines = []
        lines.append(f"Skill: **{profile.get('skill', 1)}**")
        lines.append(f"Tier: **{profile.get('tier', 1)}**")
        lines.append(f"XP: **{profile.get('xp', 0)}**")
        lines.append(f"Trace: **{profile.get('trace', 0)} / 30**")
        lines.append(f"Reputation: **{profile.get('reputation', 0)}**")
        lines.append(f"Streak: **{profile.get('streak', 0)}**")
        return "\n".join(lines)

    async def animate_chain(
        self,
        message: discord.Message,
        target: str,
        modules: Dict[str, Dict[str, Any]],
        difficulty: int,
    ):
        phases_order = [
            ("recon", "Reconnaissance", "📡", ["Mapping surface endpoints", "Profiling banners", "Fingerprinting defenses", "Constructing topology graph"]),
            ("access", "Access Vector", "🧬", ["Normalizing credentials space", "Aligning solver heuristic", "Distorting auth telemetry", "Threading exploit probes"]),
            ("payload", "Payload Orchestration", "💾", ["Assembling payload segments", "Packing and compressing", "Obfuscating signatures", "Priming execution hooks"]),
            ("extraction", "Exfiltration", "🚀", ["Splitting data streams", "Braiding proxy routes", "Masking traffic envelopes", "Sealing ghost channels"]),
        ]
        base_embed = message.embeds[0]
        for key, display, icon, steps in phases_order:
            for i in range(len(steps)):
                rows = []
                for idx, step in enumerate(steps):
                    prefix = "⚪"
                    if idx < i:
                        prefix = "✅"
                    elif idx == i:
                        prefix = "🟡"
                    rows.append(f"{prefix} {step}")
                phase_module = modules.get(key)
                module_label = phase_module["filename"] if phase_module else "no module"
                embed = discord.Embed(
                    title=f"{icon} {display} → {target}",
                    description="\n".join(rows),
                    color=discord.Color.blurple(),
                )
                embed.add_field(name="Active Module", value=f"`{module_label}`", inline=False)
                embed.add_field(name="Difficulty", value=str(difficulty), inline=True)
                await message.edit(embed=embed)
                await asyncio.sleep(0.6)

    def build_final_embed(
        self,
        user: discord.abc.User,
        target: str,
        modules: Dict[str, Dict[str, Any]],
        profile: Dict[str, Any],
        difficulty: int,
        phase_results: List[Dict[str, Any]],
        outcome: Dict[str, Any],
        progression: Dict[str, Any],
    ) -> discord.Embed:
        success = outcome["success"]
        if success:
            title = f"✅ Hack Complete: {target}"
            color = discord.Color.green()
        else:
            title = f"❌ Hack Disrupted: {target}"
            color = discord.Color.red()
        desc_lines = []
        name_map = {
            "recon": "Reconnaissance",
            "access": "Access",
            "payload": "Payload",
            "extraction": "Extraction",
        }
        for res in phase_results:
            label = name_map.get(res["phase"], res["phase"].title())
            symbol = "✅" if res["success"] else "❌"
            if res["quality"] == "flawless":
                symbol = "💎"
            elif res["quality"] == "barely":
                symbol = "⚠️" if res["success"] else symbol
            elif res["quality"] == "almost":
                symbol = "⚠️"
            margin_pct = res["margin"] / max(1.0, res["threshold"])
            margin_pct = max(-1.0, min(1.0, margin_pct))
            module_name = res["module"]["filename"] if res["module"] else "no module"
            desc_lines.append(
                f"{symbol} {label} | module `{module_name}` | power {res['power']:.1f} vs {res['threshold']:.1f} ({margin_pct*100:.1f}%) → {res['quality']}"
            )
        summary = "\n".join(desc_lines) if desc_lines else "No phases were evaluated."
        embed = discord.Embed(title=title, description=summary, color=color)
        outcome_lines = []
        if success:
            if outcome["quality"] == "perfect_chain":
                outcome_lines.append("Chain rating: **Perfect execution**")
            elif outcome["quality"] == "strong":
                outcome_lines.append("Chain rating: **Strong compromise**")
            elif outcome["quality"] == "clean":
                outcome_lines.append("Chain rating: **Clean breach**")
            elif outcome["quality"] == "shaky":
                outcome_lines.append("Chain rating: **Shaky but successful**")
            else:
                outcome_lines.append(f"Chain rating: **{outcome['quality']}**")
        else:
            if outcome["quality"] == "near_miss":
                outcome_lines.append("Chain rating: **Near miss**")
            elif outcome["quality"] == "catastrophic":
                outcome_lines.append("Chain rating: **Catastrophic failure**")
            else:
                outcome_lines.append(f"Chain rating: **{outcome['quality']}**")
        outcome_lines.append(f"XP change: **+{progression['xp_gain']}**")
        sd = progression["skill_delta"]
        rd = progression["rep_delta"]
        td = progression["trace_delta"]
        sd_str = f"{'+' if sd >= 0 else ''}{sd}"
        rd_str = f"{'+' if rd >= 0 else ''}{rd}"
        td_str = f"{'+' if td >= 0 else ''}{td}"
        outcome_lines.append(f"Skill change: **{sd_str}**")
        outcome_lines.append(f"Reputation change: **{rd_str}**")
        outcome_lines.append(f"Trace change: **{td_str}**")
        if abs(outcome["synergy_bonus"]) > 0.0:
            bonus_pct = int(outcome["synergy_bonus"] * 100)
            outcome_lines.append(f"Module synergy bonus: **{bonus_pct}%** to chain cohesion")
        embed.add_field(name="Outcome", value="\n".join(outcome_lines), inline=False)
        embed.add_field(name="Modules", value=self.format_module_summary(modules), inline=False)
        embed.add_field(name="Hacker Status", value=self.format_profile_status(profile), inline=False)
        embed.set_footer(text=f"Hacker ID: {user.id} • Difficulty: {difficulty}")
        return embed

    @app_commands.command(name="hack", description="Execute a deeply code-based multi-phase hacking run.")
    @app_commands.describe(
        target="Target system identifier",
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
        recon_file: Optional[str] = None,
        access_file: Optional[str] = None,
        payload_file: Optional[str] = None,
        extract_file: Optional[str] = None,
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
                    await interaction.response.send_message(
                        f"⏳ Your rigs are recalibrating. Try again in **{int(remaining)}s**.",
                        ephemeral=True,
                    )
                    return
        profile["last_hack"] = now.isoformat()
        save_state()
        pad = self.get_user_pad(user.id)
        modules = self.select_modules(
            pad,
            recon_file,
            access_file,
            payload_file,
            extract_file,
        )
        if not modules["recon"] and not modules["access"] and not modules["payload"] and not modules["extraction"]:
            await interaction.response.send_message(
                "❌ No usable scripts found in your codepad. Create some with `/code_new` and `/code_edit` first.",
                ephemeral=True,
            )
            return
        await interaction.response.defer()
        base_embed = discord.Embed(
            title=f"Initializing Hack Plan → {target}",
            description="Constructing phase chain from your scripts...",
            color=discord.Color.blurple(),
        )
        base_embed.add_field(name="Hacker Status", value=self.format_profile_status(profile), inline=False)
        base_embed.add_field(name="Modules", value=self.format_module_summary(modules), inline=False)
        diff_prof = self.difficulty_profile(difficulty)
        diff_desc = []
        diff_desc.append(f"Security integrity: **{diff_prof['security_integrity']:.1f}**")
        diff_desc.append(f"Anomaly detection: **{diff_prof['anomaly_detection']:.1f}**")
        diff_desc.append(f"Bandwidth pressure: **{diff_prof['bandwidth_pressure']:.1f}**")
        diff_desc.append(f"Forensic risk: **{diff_prof['forensic_risk']:.1f}**")
        base_embed.add_field(name="Target Profile", value="\n".join(diff_desc), inline=False)
        msg = await interaction.followup.send(embed=base_embed)
        await self.animate_chain(msg, target, modules, difficulty)
        profile_mod = self.compute_profile_modifiers(profile)
        recon_res = self.compute_phase_score("recon", modules.get("recon"), profile_mod, diff_prof, profile)
        access_res = self.compute_phase_score("access", modules.get("access"), profile_mod, diff_prof, profile)
        payload_res = self.compute_phase_score("payload", modules.get("payload"), profile_mod, diff_prof, profile)
        extract_res = self.compute_phase_score("extraction", modules.get("extraction"), profile_mod, diff_prof, profile)
        phase_results = [recon_res, access_res, payload_res, extract_res]
        outcome = self.aggregate_outcome(phase_results)
        progression = self.apply_progression(profile, difficulty, outcome, phase_results)
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
        profile["hack_history"] = profile["hack_history"][-20:]
        save_state()
        final_embed = self.build_final_embed(
            user,
            target,
            modules,
            profile,
            difficulty,
            phase_results,
            outcome,
            progression,
        )
        await msg.edit(embed=final_embed)


async def setup(bot):
    await bot.add_cog(HackerRPG(bot))
