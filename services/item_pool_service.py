"""Non-repeater item pool and 2-day difference tracking service for SSB Practice Studio.
Implements persistent cycles, automatic shuffling upon exhaustion, and 2-day history exclusion.
Developed by Lt. V. Elangovan
"""

import json
import logging
import random
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# 60 Standard WAT Words with Unique IDs
WAT_WORDS_BANK = [
    {"id": f"wat-{i+1:02d}", "word": word, "category": cat}
    for i, (word, cat) in enumerate([
        ("COURAGE", "Dynamic: Courage"),
        ("RESPONSIBLE", "Social: Responsibility"),
        ("INITIATIVE", "Social: Initiative"),
        ("LEADER", "Social: Leadership"),
        ("COOPERATION", "Social: Cooperation"),
        ("DETERMINATION", "Dynamic: Determination"),
        ("SPEED", "Planning: Speed of Decision"),
        ("ALERT", "Intelligence: Vigilance"),
        ("SOLVE", "Reasoning Ability"),
        ("HELP", "Social Adaptability"),
        ("FRIENDS", "Social Adaptability"),
        ("DIFFICULT", "Dynamic: Courage"),
        ("WAR", "Fighting Spirit"),
        ("PEACE", "Social Effectiveness"),
        ("ENEMY", "Dynamic: Courage"),
        ("VICTORY", "Determination"),
        ("JUNGLE", "Endurance & Fieldcraft"),
        ("RIVER", "Initiative & Resourcefulness"),
        ("NIGHT", "Vigilance"),
        ("BRAVERY", "Dynamic: Courage"),
        ("HONOUR", "Moral Integrity"),
        ("DISCIPLINE", "Social Effectiveness"),
        ("TEAM", "Cooperation & Unity"),
        ("DUTY", "Sense of Responsibility"),
        ("COUNTRY", "Patriotism"),
        ("YOUTH", "Energy & Stamina"),
        ("CHALLENGE", "Determination"),
        ("DECISION", "Quickness of Decision"),
        ("TRUST", "Social Effectiveness"),
        ("HARDWORK", "Determination"),
        ("SUCCESS", "Achievement Drive"),
        ("FEAR", "Courage & Self-Control"),
        ("DANGER", "Dynamic: Courage"),
        ("SYSTEM", "Organizing Ability"),
        ("LAW", "Social Effectiveness"),
        ("ORDER", "Organizing Ability"),
        ("SOCIETY", "Social Adaptability"),
        ("FUTURE", "Planning & Vision"),
        ("TARGET", "Determination"),
        ("EFFORT", "Endurance"),
        ("STRATEGY", "Planning Ability"),
        ("ATTACK", "Initiative"),
        ("PLAN", "Organizing Ability"),
        ("ACTION", "Dynamic: Initiative"),
        ("FAITH", "Self Confidence"),
        ("CALM", "Emotional Stability"),
        ("PATIENCE", "Emotional Stability"),
        ("ENERGY", "Dynamic Stamina"),
        ("MORAL", "Integrity"),
        ("DEFENCE", "Fighting Spirit"),
        ("HONESTY", "Integrity"),
        ("SACRIFICE", "Courage"),
        ("VIOLENCE", "Emotional Stability"),
        ("SOLDIER", "Fighting Spirit"),
        ("OBSTACLE", "Courage"),
        ("JUSTICE", "Integrity"),
        ("COMMAND", "Leadership"),
        ("LOYALTY", "Integrity"),
        ("PATRIOT", "Patriotism"),
        ("MISSION", "Determination"),
    ])
]

# 60 Standard SRT Situations with Rule 1 & Rule 2 preservation
SRT_SITUATIONS_BANK = [
    {
        "id": f"srt-{i+1:02d}",
        "serial": i + 1,
        "text": text,
    }
    for i, text in enumerate([
        "He was traveling in a crowded train when he noticed smoke coming from beneath the adjoining compartment. He (...)",
        "While on an evening trek in the forest with friends, one member slipped into a deep ravine and lost consciousness. He (...)",
        "His captain in the military convoy was severely wounded in an ambush and communication was cut off. He (...)",
        "He was preparing for his final degree examination when the main hostel wing caught fire. He (...)",
        "On his way to an important job interview, he saw two masked men snatch a purse from an elderly lady and flee on a motorbike. He (...)",
        "His younger brother fell into bad company and started stealing money from home. He (...)",
        "During a flood relief operation, the rescue boat developed a serious leak in the middle of a swirling river. He (...)",
        "His team was assigned a difficult reconnaissance patrol behind enemy lines under severe blizzard conditions. He (...)",
        "He arrived at the railway station for a crucial journey only to find his wallet and ticket had been stolen. He (...)",
        "While swimming in the river, his friend was caught in a strong whirlpool and shouted for help. He (...)",
        "A colleague in his office was falsely accusing him of financial misappropriation to senior management. He (...)",
        "The bridge connecting his village to the nearest hospital was washed away while a villager needed emergency surgery. He (...)",
        "He was leading a night patrol along the border fence when he spotted three armed intruders attempting to breach. He (...)",
        "During a college agitation, violent protestors tried to force open his laboratory doors and damage costly research equipment. He (...)",
        "He was on a high-altitude expedition when the weather turned ferocious, his compass broke, and his radio lost signal. He (...)",
        "In an inter-academy championship match, his team required 18 runs in the final over with only two wickets remaining. He (...)",
        "A massive landslide blocked the highway pass, trapping a bus full of passengers in freezing sub-zero cold. He (...)",
        "While walking through a deserted street late at night, he found an injured soldier lying unconscious on the sidewalk. He (...)",
        "His parents wanted him to take over the family business, but his lifelong ambition was to serve as an officer in the Armed Forces. He (...)",
        "In the middle of an intensive tactical field exercise, his group leader became incapacitated with acute appendicitis. He (...)",
        "While traveling on a night train, he woke up to discover two armed dacoits holding the passengers hostage at gunpoint. He (...)",
        "He noticed that the storekeeper in his regiment was secretly selling defense rations in the civilian black market. He (...)",
        "During a village sports tournament, a communal brawl erupted among spectators threatening widespread violence. He (...)",
        "His boat capsized in the middle of a lake and his companion did not know how to swim. He (...)",
        "He was driving on a desolate highway at night when a speeding truck hit a scooterist and fled without stopping. He (...)",
        "He received emergency orders to report for duty immediately, but his mother had just been admitted to the ICU with chest pain. He (...)",
        "While crossing a railway track, he noticed a large crack in the rail and heard the distant horn of an approaching passenger express. He (...)",
        "His close friend asked him to leak the confidential questions for the upcoming departmental entrance exam. He (...)",
        "While on a mountain trek, his group exhausted their food supply and the nearest village was two days away. He (...)",
        "During an outdoor firing practice, an accidental stray round severely injured a fellow cadet next to him. He (...)",
        "He was traveling in a city bus when three rowdies started harassing a college girl sitting nearby. He (...)",
        "His superior officer gave an operational order that he realized was based on outdated tactical intelligence and could lead to disaster. He (...)",
        "During a cyclone, a high-voltage electrical line snapped and fell onto a waterlogged street where children were stranded. He (...)",
        "He was selected for an international military training course, but his teammate challenged the selection claiming bias. He (...)",
        "While on jungle warfare training, his squad was encircled by hostile armed insurgents. He (...)",
        "He lost his service identity card and movement order documents at an overcrowded junction while in uniform. He (...)",
        "A fire broke out in an ammunition depot where he was performing guard duty. He (...)",
        "His team members lost morale and refused to continue an exhausting 40-kilometer endurance march. He (...)",
        "While on leave in his village, he found moneylenders exploiting illiterate farmers through fraudulent contracts. He (...)",
        "He discovered a ticking suspicious package left unattended on a crowded metro station platform. He (...)",
        "During a field tactical exercise, heavy fog separated him from the main battalion in enemy territory. He (...)",
        "A fellow candidate during the SSB interview group task was dominating constantly and not letting others speak. He (...)",
        "His roommate in the hostel was severely addicted to drugs and was deteriorating rapidly. He (...)",
        "While crossing a desert tract, their patrol vehicle suffered a broken radiator and the water supply was nearly empty. He (...)",
        "In an examination hall, the invigilator falsely accused him of copying from a concealed slip. He (...)",
        "He saw a pickpocket steal a passenger's wallet in a crowded market and slip into a narrow dark alley. He (...)",
        "While leading a disaster relief column, angry flood victims blocked the road demanding immediate food distribution. He (...)",
        "His colleague in the military engineering wing was taking bribes to clear substandard construction material. He (...)",
        "On the day of his final SSB interview, his train was delayed by four hours due to engine failure. He (...)",
        "During a night navigation exercise, his group's only GPS device fell into a swift stream and was lost. He (...)",
        "He noticed his squad partner had forgotten his weapon on a forward observation post. He (...)",
        "During a village night patrol, a venomous snake bit his companion on the ankle. He (...)",
        "A sudden gas cylinder explosion took place in his neighbor's house creating thick smoke and screams. He (...)",
        "While crossing a suspension bridge during a storm, several cables snapped, leaving three civilians dangling. He (...)",
        "His team captain was disqualified right before the inter-services debate final. He (...)",
        "He was tasked with organizing security for a high-level visiting dignitary with only 6 hours notice. He (...)",
        "He found out that rumors were being deliberately spread to demoralize his platoon before a decisive tactical drill. He (...)",
        "His parachute drifted into hostile tree canopy terrain far away from the drop zone. He (...)",
        "A junior cadet broke down crying from exhaustion and fear during a high-obstacle night rope course. He (...)",
        "He was ordered to lead a dawn patrol mission across a newly mined valley with incomplete maps. He (...)",
    ])
]

# 12 Standard TAT Picture Prompts
TAT_SCENES_BANK = [
    {"id": f"tat-{i+1:02d}", "title": t, "desc": d, "is_blank": (i == 11)}
    for i, (t, d) in enumerate([
        ("Tactical Night Map Conference", "A young officer studying a map under lamplight with two comrades in forward bunker."),
        ("Embankment Breach & Flood Rescue", "Villagers gathered near a breached river embankment pointing towards rising floodwaters."),
        ("Industrial Plant Machinery Overhaul", "An engineer examining blueprint machinery in a bustling industrial manufacturing plant."),
        ("High-Altitude Mountain Ascent", "A squad of mountaineers ascending an icy ridge amidst gathering blizzard clouds."),
        ("Medical Camp in Remote Outpost", "A young doctor coordinating emergency supplies as villagers arrive on stretchers."),
        ("Village Meeting Under Banyan Tree", "Youth leader addressing an attentive village council discussing road development."),
        ("Forward Bunker Observation Post", "Two sentries standing vigil through optical binoculars along an electrified border fence."),
        ("Scientific Laboratory Experiment", "Two researchers intensely analyzing chemical test tubes in an advanced laboratory setting."),
        ("Agricultural Irrigation Project", "A young agricultural officer demonstrating drip irrigation equipment to local farmers."),
        ("Highway Accident Quick Response", "A commuter directing traffic and organizing first-aid for victims of an overturned car."),
        ("Helicopter Relief Drop Operation", "Armed forces rescue personnel loading crates into a hovering relief helicopter."),
        ("Official Blank Slide (Picture #12)", "Blank Slide — Project your own positive, officer-like story with a decisive hero."),
    ])
]


class ItemPoolService:
    """Manages persistent non-repeater rotation and 2-day history exclusions."""

    def __init__(self, ctx) -> None:
        self.ctx = ctx
        self.banks = {
            "wat": WAT_WORDS_BANK,
            "srt": SRT_SITUATIONS_BANK,
            "tat": TAT_SCENES_BANK,
        }

    def _get_last_2_days_dates(self) -> List[str]:
        today = date.today()
        yesterday = today - timedelta(days=1)
        return [today.isoformat(), yesterday.isoformat()]

    def _get_history(self) -> List[Dict[str, Any]]:
        raw = self.ctx.get_setting("item_pool_history", "[]")
        try:
            return json.loads(raw)
        except Exception:
            return []

    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        trimmed = history[-500:]
        self.ctx.set_setting("item_pool_history", json.dumps(trimmed))

    def _get_cycles(self) -> Dict[str, List[str]]:
        raw = self.ctx.get_setting("item_pool_cycles", "{}")
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {}

    def _save_cycles(self, cycles: Dict[str, List[str]]) -> None:
        self.ctx.set_setting("item_pool_cycles", json.dumps(cycles))

    def get_last_2_days_item_ids(self, test_type: Optional[str] = None) -> Set[str]:
        target_dates = set(self._get_last_2_days_dates())
        history = self._get_history()
        excluded = set()
        for item in history:
            if item.get("date") in target_dates:
                if not test_type or item.get("type") == test_type:
                    excluded.add(item.get("id"))
        return excluded

    def get_items(self, test_type: str, count: int = 15) -> List[Dict[str, Any]]:
        """
        Draws `count` items with:
        1. Non-repeater cycle tracking.
        2. Exclusion of items practiced in the last 2 days.
        3. Automatic shuffle once the pool is exhausted.
        """
        bank = self.banks.get(test_type.lower(), [])
        if not bank:
            return []

        item_map = {i["id"]: i for i in bank}
        cycles = self._get_cycles()
        current_pool = cycles.get(test_type.lower(), [])

        last_2_days_ids = self.get_last_2_days_item_ids(test_type.lower())

        # Candidates are unpracticed items not in the last 2 days
        candidates = [cid for cid in current_pool if cid not in last_2_days_ids]

        # If exhausted, re-seed all items, shuffle once, and begin fresh cycle!
        if len(candidates) < count:
            all_ids = [i["id"] for i in bank]
            random.shuffle(all_ids)
            fresh_candidates = [cid for cid in all_ids if cid not in last_2_days_ids]
            candidates = fresh_candidates if len(fresh_candidates) >= count else all_ids
            current_pool = all_ids

        selected_ids = candidates[:count]

        # Update remaining pool
        remaining = [cid for cid in current_pool if cid not in selected_ids]
        cycles[test_type.lower()] = remaining
        self._save_cycles(cycles)

        # Record to history with today's date
        today_str = date.today().isoformat()
        history = self._get_history()
        for sid in selected_ids:
            history.append({
                "id": sid,
                "type": test_type.lower(),
                "date": today_str,
                "timestamp": datetime.now().isoformat(),
            })
        self._save_history(history)

        return [item_map[sid] for sid in selected_ids if sid in item_map]

    def get_daily_task(self) -> Dict[str, Any]:
        """Draws 2 TAT scenes, 15 WAT words, and 15 SRT situations."""
        return {
            "date": date.today().isoformat(),
            "tat": self.get_items("tat", 2),
            "wat": self.get_items("wat", 15),
            "srt": self.get_items("srt", 15),
        }

    def record_daily_completion(self) -> int:
        today_str = date.today().isoformat()
        streak_count = self.get_streak()
        last_date = self.ctx.get_setting("daily_streak_last_date", "")

        if last_date:
            try:
                last_dt = date.fromisoformat(last_date)
                today_dt = date.today()
                diff = (today_dt - last_dt).days
                if diff == 1:
                    streak_count += 1
                elif diff > 1:
                    streak_count = 1
            except Exception:
                streak_count = 1
        else:
            streak_count = 1

        self.ctx.set_setting("daily_streak_count", streak_count)
        self.ctx.set_setting("daily_streak_last_date", today_str)
        return streak_count

    def get_streak(self) -> int:
        return int(self.ctx.get_setting("daily_streak_count", 0))

