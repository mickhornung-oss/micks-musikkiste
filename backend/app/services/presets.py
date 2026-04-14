"""Preset-Management für Micks Musikkiste V2"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from app.models import TrackPreset, BeatPreset, PresetValues


class PresetsManager:
    """Verwaltet Presets für Track- und Beat-Generierung"""
    
    def __init__(self):
        """Initialisiere Preset-Manager"""
        self.presets_dir = Path(__file__).parent.parent.parent / "data" / "presets"
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        
        # Lade oder erstelle Standard-Presets
        self._ensure_default_presets()
    
    def _ensure_default_presets(self):
        """Stelle sicher, dass Standard-Presets existieren"""
        tracks_file = self.presets_dir / "track_presets.json"
        beats_file = self.presets_dir / "beat_presets.json"
        
        if not tracks_file.exists():
            self._create_default_track_presets()
        if not beats_file.exists():
            self._create_default_beat_presets()
    
    def _create_default_track_presets(self):
        """Erstelle Standard Track-Presets"""
        presets = {
            "presets": [
                {
                    "id": "techno_dark",
                    "name": "Dark Techno",
                    "category": "techno",
                    "description": "Dunkle, hypnotische Techno mit minimalistischem Ansatz",
                    "default_mood": "dark",
                    "recommended_language": "en",
                    "recommended_duration": 240,
                    "negative_prompts": ["weak", "happy", "vocals", "bright"],
                    "style_description": "Deep, hypnotic techno with dark atmosphere. Minimal melodics. Repetitive groove.",
                    "values": {
                        "energy": 6,
                        "tempo": 125,
                        "creativity": 4,
                        "catchiness": 2,
                        "vocal_strength": 0,
                        "heaviness": 7,
                        "melody_amount": 1
                    },
                    "tags": ["techno", "dark", "minimal"]
                },
                {
                    "id": "techno_melodic",
                    "name": "Melodic Techno",
                    "category": "techno",
                    "description": "Melodische Techno mit emotionalem Touch",
                    "default_mood": "energetic",
                    "recommended_language": "en",
                    "recommended_duration": 240,
                    "negative_prompts": ["harsh", "too dark", "weak"],
                    "style_description": "Melodic techno with emotional element. Well-structured. Good groove.",
                    "values": {
                        "energy": 7,
                        "tempo": 130,
                        "creativity": 6,
                        "catchiness": 6,
                        "vocal_strength": 2,
                        "heaviness": 5,
                        "melody_amount": 7
                    },
                    "tags": ["techno", "melodic", "emotional"]
                },
                {
                    "id": "techno_club",
                    "name": "Driving Club Techno",
                    "category": "techno",
                    "description": "Energische Club-Techno zum Tanzen",
                    "default_mood": "energetic",
                    "recommended_language": "en",
                    "recommended_duration": 240,
                    "negative_prompts": ["weak", "slow", "quiet"],
                    "style_description": "Driving club techno. Powerful beat. High energy. Dance floor ready.",
                    "values": {
                        "energy": 9,
                        "tempo": 135,
                        "creativity": 5,
                        "catchiness": 5,
                        "vocal_strength": 1,
                        "heaviness": 8,
                        "melody_amount": 3
                    },
                    "tags": ["techno", "club", "dance"]
                },
                {
                    "id": "techno_hard",
                    "name": "Hard Underground Techno",
                    "category": "techno",
                    "description": "Harte, raue Underground-Techno",
                    "default_mood": "dark",
                    "recommended_language": "en",
                    "recommended_duration": 240,
                    "negative_prompts": ["soft", "pleasant", "clean"],
                    "style_description": "Hard, raw underground techno. Harsh sounds. Industrial edge. Aggressive.",
                    "values": {
                        "energy": 10,
                        "tempo": 145,
                        "creativity": 7,
                        "catchiness": 1,
                        "vocal_strength": 0,
                        "heaviness": 10,
                        "melody_amount": 0
                    },
                    "tags": ["techno", "hard", "underground"]
                },
                {
                    "id": "hiphop_boombap",
                    "name": "Boom Bap",
                    "category": "hiphop",
                    "description": "Klassisches Boom Bap mit sauberer Schlagzeug und Sampling",
                    "default_mood": "neutral",
                    "recommended_language": "en",
                    "recommended_duration": 180,
                    "negative_prompts": ["trap hats", "edm risers", "four on the floor", "too modern"],
                    "style_description": "Classic boom bap with dusty drums, chopped soul texture, strong snare and head-nod groove.",
                    "values": {
                        "energy": 5,
                        "tempo": 95,
                        "creativity": 6,
                        "catchiness": 7,
                        "vocal_strength": 5,
                        "heaviness": 6,
                        "melody_amount": 4
                    },
                    "tags": ["hiphop", "boom bap", "dusty drums", "head nod"]
                },
                {
                    "id": "hiphop_trap",
                    "name": "Modern Trap",
                    "category": "hiphop",
                    "description": "Modernes Trap mit 808s und schnellen Hats",
                    "default_mood": "energetic",
                    "recommended_language": "en",
                    "recommended_duration": 180,
                    "negative_prompts": ["boom bap swing", "rock guitars", "euphoric trance"],
                    "style_description": "Modern trap with heavy 808 sub, fast hats, dark space and punchy street energy.",
                    "values": {
                        "energy": 9,
                        "tempo": 100,
                        "creativity": 6,
                        "catchiness": 7,
                        "vocal_strength": 4,
                        "heaviness": 9,
                        "melody_amount": 2
                    },
                    "tags": ["hiphop", "trap", "808", "dark"]
                },
                {
                    "id": "hiphop_lofi",
                    "name": "LoFi Hip-Hop",
                    "category": "hiphop",
                    "description": "Entspannte LoFi Hip-Hop mit Vinyl-Qualität",
                    "default_mood": "calm",
                    "recommended_language": "en",
                    "recommended_duration": 240,
                    "negative_prompts": ["loud", "aggressive", "modern"],
                    "style_description": "Relaxed lo-fi hip-hop. Vinyl sound. Chill vibes. Study music.",
                    "values": {
                        "energy": 3,
                        "tempo": 85,
                        "creativity": 5,
                        "catchiness": 4,
                        "vocal_strength": 2,
                        "heaviness": 2,
                        "melody_amount": 7
                    },
                    "tags": ["hiphop", "lofi", "chill"]
                },
                {
                    "id": "hiphop_dark",
                    "name": "Dark Urban Hip-Hop",
                    "category": "hiphop",
                    "description": "Düsteres Urban Hip-Hop mit aggressivem Edge",
                    "default_mood": "dark",
                    "recommended_language": "en",
                    "recommended_duration": 180,
                    "negative_prompts": ["happy", "bright", "soft", "pop chorus"],
                    "style_description": "Dark urban hip-hop with sparse piano, deep sub, hard drums and tense street atmosphere.",
                    "values": {
                        "energy": 8,
                        "tempo": 92,
                        "creativity": 6,
                        "catchiness": 5,
                        "vocal_strength": 6,
                        "heaviness": 9,
                        "melody_amount": 2
                    },
                    "tags": ["hiphop", "dark", "urban", "808"]
                }
            ]
        }
        
        presets_file = self.presets_dir / "track_presets.json"
        with presets_file.open("w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2, ensure_ascii=False)
    
    def _create_default_beat_presets(self):
        """Erstelle Standard Beat-Presets"""
        presets = {
            "presets": [
                {
                    "id": "beat_techno_dark",
                    "name": "Dark Techno Beat",
                    "category": "techno",
                    "description": "Dunkler Trommel-Pattern für Techno",
                    "default_mood": "dark",
                    "recommended_duration": 240,
                    "recommended_tempo": 125,
                    "negative_prompts": ["happy", "bright"],
                    "style_description": "Dark minimal beat. Hypnotic groove. Techno foundation.",
                    "drum_kit_hint": "analog",
                    "values": {
                        "energy": 6,
                        "tempo": 125,
                        "creativity": 3,
                        "catchiness": 1,
                        "vocal_strength": 0,
                        "heaviness": 7,
                        "melody_amount": 0
                    },
                    "tags": ["techno", "beat", "dark"]
                },
                {
                    "id": "beat_techno_club",
                    "name": "Club Techno Beat",
                    "category": "techno",
                    "description": "Clubbiger Trommel-Pattern",
                    "default_mood": "energetic",
                    "recommended_duration": 240,
                    "recommended_tempo": 128,
                    "negative_prompts": ["weak", "quiet"],
                    "style_description": "Club techno beat. Strong kick. Dance floor ready.",
                    "drum_kit_hint": "electronic",
                    "values": {
                        "energy": 8,
                        "tempo": 128,
                        "creativity": 4,
                        "catchiness": 2,
                        "vocal_strength": 0,
                        "heaviness": 8,
                        "melody_amount": 1
                    },
                    "tags": ["techno", "beat", "club"]
                },
                {
                    "id": "beat_hiphop_boom",
                    "name": "Boom Bap Beat",
                    "category": "hiphop",
                    "description": "Klassischer Boom Bap Pattern",
                    "default_mood": "neutral",
                    "recommended_duration": 180,
                    "recommended_tempo": 95,
                    "negative_prompts": ["trap hats", "techno kick", "edm riser", "overcompressed"],
                    "style_description": "Classic boom bap beat with dusty drums, chopped sample feel, strong snare and head-nod pocket.",
                    "drum_kit_hint": "vintage",
                    "values": {
                        "energy": 5,
                        "tempo": 95,
                        "creativity": 5,
                        "catchiness": 6,
                        "vocal_strength": 0,
                        "heaviness": 5,
                        "melody_amount": 2
                    },
                    "tags": ["hiphop", "boom bap", "dusty drums", "head nod"]
                },
                {
                    "id": "beat_hiphop_trap",
                    "name": "Trap Beat",
                    "category": "hiphop",
                    "description": "Moderner Trap-Trommel-Pattern",
                    "default_mood": "energetic",
                    "recommended_duration": 180,
                    "recommended_tempo": 100,
                    "negative_prompts": ["boom bap swing", "jazzy samples", "trance leads"],
                    "style_description": "Modern trap beat with heavy 808 glide, tight hats, sparse melody and dark modern bounce.",
                    "drum_kit_hint": "808",
                    "values": {
                        "energy": 9,
                        "tempo": 100,
                        "creativity": 4,
                        "catchiness": 6,
                        "vocal_strength": 0,
                        "heaviness": 9,
                        "melody_amount": 0
                    },
                    "tags": ["hiphop", "trap", "808", "dark bounce"]
                }
            ]
        }
        
        presets_file = self.presets_dir / "beat_presets.json"
        with presets_file.open("w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2, ensure_ascii=False)
    
    def get_track_presets(self, category: Optional[str] = None) -> List[Dict]:
        """Hole Track-Presets"""
        try:
            presets_file = self.presets_dir / "track_presets.json"
            if presets_file.exists():
                with presets_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    presets = data.get("presets", [])
                    
                    if category:
                        presets = [p for p in presets if p.get("category") == category]
                    
                    return presets
        except Exception as e:
            print(f"Fehler beim Laden von Track-Presets: {e}")
        
        return []
    
    def get_beat_presets(self, category: Optional[str] = None) -> List[Dict]:
        """Hole Beat-Presets"""
        try:
            presets_file = self.presets_dir / "beat_presets.json"
            if presets_file.exists():
                with presets_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    presets = data.get("presets", [])
                    
                    if category:
                        presets = [p for p in presets if p.get("category") == category]
                    
                    return presets
        except Exception as e:
            print(f"Fehler beim Laden von Beat-Presets: {e}")
        
        return []
    
    def get_track_preset(self, preset_id: str) -> Optional[Dict]:
        """Hole ein spezifisches Track-Preset"""
        presets = self.get_track_presets()
        for preset in presets:
            if preset.get("id") == preset_id:
                return preset
        return None
    
    def get_beat_preset(self, preset_id: str) -> Optional[Dict]:
        """Hole ein spezifisches Beat-Preset"""
        presets = self.get_beat_presets()
        for preset in presets:
            if preset.get("id") == preset_id:
                return preset
        return None

    @staticmethod
    def _merge_unique_strings(existing: list | None, additions: list | None) -> list:
        merged = []
        for value in (existing or []) + (additions or []):
            text = str(value).strip()
            if text and text not in merged:
                merged.append(text)
        return merged
    
    def apply_track_preset(self, preset_id: str, request_data: dict) -> dict:
        """Wende ein Track-Preset auf Request-Daten an"""
        preset = self.get_track_preset(preset_id)
        if not preset:
            return request_data
        
        # Überschreibe mit Preset-Werten (aber nur wenn nicht explizit gesetzt)
        values = preset.get("values", {})
        
        # Setze Preset-Defaults nur wenn nicht explizit in Request vorhanden
        if "energy" not in request_data or request_data["energy"] == 5:
            request_data["energy"] = values.get("energy", 5)
        if "tempo" not in request_data or request_data["tempo"] == 120:
            request_data["tempo"] = values.get("tempo", 120)
        if "creativity" not in request_data or request_data["creativity"] == 5:
            request_data["creativity"] = values.get("creativity", 5)
        if "catchiness" not in request_data or request_data["catchiness"] == 5:
            request_data["catchiness"] = values.get("catchiness", 5)
        if "vocal_strength" not in request_data or request_data["vocal_strength"] == 5:
            request_data["vocal_strength"] = values.get("vocal_strength", 5)
        
        # Kombiniere negative Prompts
        request_data["negative_prompts"] = self._merge_unique_strings(
            request_data.get("negative_prompts"),
            preset.get("negative_prompts", []),
        )
        request_data["style_description"] = preset.get("style_description", "")
        request_data["preset_tags"] = self._merge_unique_strings(
            request_data.get("preset_tags"),
            preset.get("tags", []),
        )
        request_data["generation_mode"] = "full_track"
        request_data["instrumental_preferred"] = int(request_data.get("vocal_strength", values.get("vocal_strength", 5))) <= 1

        # Speichere Preset-ID
        request_data["preset_used"] = preset_id
        
        return request_data
    
    def apply_beat_preset(self, preset_id: str, request_data: dict) -> dict:
        """Wende ein Beat-Preset auf Request-Daten an"""
        preset = self.get_beat_preset(preset_id)
        if not preset:
            return request_data
        
        # Ähnliche Logik wie bei Track-Presets
        values = preset.get("values", {})
        
        if "energy" not in request_data or request_data["energy"] == 6:
            request_data["energy"] = values.get("energy", 6)
        if "tempo" not in request_data or request_data["tempo"] == 120:
            request_data["tempo"] = values.get("tempo", 120)
        if "heaviness" not in request_data or request_data["heaviness"] == 5:
            request_data["heaviness"] = values.get("heaviness", 5)
        if "melody_amount" not in request_data or request_data["melody_amount"] == 3:
            request_data["melody_amount"] = values.get("melody_amount", 3)
        
        request_data["negative_prompts"] = self._merge_unique_strings(
            request_data.get("negative_prompts"),
            preset.get("negative_prompts", []),
        )
        request_data["style_description"] = preset.get("style_description", "")
        request_data["preset_tags"] = self._merge_unique_strings(
            request_data.get("preset_tags"),
            preset.get("tags", []),
        )
        request_data["drum_kit_hint"] = preset.get("drum_kit_hint")
        request_data["generation_mode"] = "beat"
        request_data["instrumental_preferred"] = True

        request_data["preset_used"] = preset_id
        
        return request_data


# Globale Instanz
presets_manager = PresetsManager()
