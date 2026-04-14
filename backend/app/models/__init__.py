"""Datenmodelle für Micks Musikkiste"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class PresetValues(BaseModel):
    """Basis-Werte für Presets"""
    energy: int = Field(default=5, ge=1, le=10)
    tempo: int = Field(default=120, ge=60, le=180)
    creativity: int = Field(default=5, ge=1, le=10)
    catchiness: int = Field(default=5, ge=1, le=10)
    vocal_strength: int = Field(default=5, ge=0, le=10)
    heaviness: int = Field(default=5, ge=1, le=10)
    melody_amount: int = Field(default=3, ge=0, le=10)


class TrackPreset(BaseModel):
    """Preset für Track-Generierung"""
    id: str
    name: str
    category: str = Field(..., description="Kategorie: techno, hiphop, etc.")
    description: str
    default_mood: str
    recommended_language: str = "en"
    recommended_duration: int = 120
    negative_prompts: List[str] = Field(default_factory=list)
    style_description: str  # Für Prompt an Engine
    values: PresetValues
    tags: List[str] = Field(default_factory=list)


class BeatPreset(BaseModel):
    """Preset für Beat-Generierung"""
    id: str
    name: str
    category: str = Field(..., description="Kategorie: techno, hiphop, etc.")
    description: str
    default_mood: str
    recommended_duration: int = 120
    recommended_tempo: int = 120
    negative_prompts: List[str] = Field(default_factory=list)
    style_description: str
    values: PresetValues
    drum_kit_hint: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class TrackGenerationRequest(BaseModel):
    """Request-Modell für Track-Generierung (V2: mit Preset)"""
    title: str = Field(..., min_length=1, max_length=100)
    genre: str = Field(..., description="z.B. Techno, Hip-Hop, House")
    mood: str = Field(default="neutral", description="z.B. energetic, melancholic, dark")
    language: str = Field(default="en", description="Sprache für Vocals")
    duration: int = Field(default=120, ge=30, le=600, description="Dauer in Sekunden")
    lyrics: Optional[str] = Field(None, description="Text-Idee oder Lyrics")
    negative_prompts: Optional[List[str]] = Field(default_factory=list)
    preset_id: Optional[str] = Field(None, description="Optionales Preset-ID")
    
    # Regler
    energy: int = Field(default=5, ge=1, le=10)
    tempo: int = Field(default=120, ge=60, le=180)
    creativity: int = Field(default=5, ge=1, le=10)
    catchiness: int = Field(default=5, ge=1, le=10)
    vocal_strength: int = Field(default=5, ge=0, le=10)


class BeatGenerationRequest(BaseModel):
    """Request-Modell für Beat-Generierung (V2: mit Preset)"""
    title: str = Field(..., min_length=1, max_length=100)
    genre: str = Field(..., description="z.B. Techno, Hip-Hop")
    mood: str = Field(default="dark", description="z.B. hard, groovy, minimalist")
    duration: int = Field(default=120, ge=30, le=600, description="Dauer in Sekunden")
    preset_id: Optional[str] = Field(None, description="Optionales Preset-ID")
    
    # Regler
    tempo: int = Field(default=120, ge=60, le=180)
    heaviness: int = Field(default=5, ge=1, le=10, description="Druck/Härte")
    melody_amount: int = Field(default=3, ge=0, le=10)
    energy: int = Field(default=6, ge=1, le=10)


class GenerationJob(BaseModel):
    """Modell für Generierungs-Job (V2: mit erweiterten States)"""
    id: str
    type: str = Field(..., description="track oder beat")
    title: str
    created_at: datetime
    status: str = Field(default="pending", description="pending, queued, generating, completed, failed, cancelled")
    progress: int = Field(default=0, ge=0, le=100)
    error: Optional[str] = None
    result_file: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    preset_used: Optional[str] = None


class Project(BaseModel):
    """Modell für ein gespeichertes Projekt (V2: erweitert)"""
    id: str
    name: str
    type: str = Field(..., description="track oder beat")
    genre: str
    mood: str
    duration: int
    created_at: datetime
    updated_at: datetime
    data_file: str = Field(..., description="Pfad zur Projektdatei")
    output_file: Optional[str] = None
    preset_used: Optional[str] = None
    lyrics: Optional[str] = None
    negative_prompts: Optional[List[str]] = None
    notes: Optional[str] = None
    parameters: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    exports: List[Dict[str, str]] = Field(default_factory=list)
    last_export_at: Optional[datetime] = None


class SaveProjectRequest(BaseModel):
    """Request für das Anlegen eines Projekts (V2 Phase 2)"""
    name: str
    project_type: str
    genre: str
    mood: str
    duration: int = 120
    output_file: Optional[str] = None
    preset_used: Optional[str] = None
    lyrics: Optional[str] = None
    negative_prompts: Optional[List[str]] = Field(default_factory=list)
    parameters: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class SystemStatus(BaseModel):
    """System-Status Modell"""
    status: str = Field(default="ok")
    engine_type: str
    engine_name: str = Field(default="unknown")
    version: str
    data_dir_ok: bool = True
    total_projects: int = 0
    total_outputs: int = 0


class DiagnosticsResponse(BaseModel):
    """Diagnose-Daten fuer lokalen Betrieb."""
    status: str = Field(default="ok")
    version: str
    engine_type: str
    engine: dict = Field(default_factory=dict)
    database: dict = Field(default_factory=dict)
    jobs: dict = Field(default_factory=dict)
    worker: dict = Field(default_factory=dict)
    runtime: dict = Field(default_factory=dict)
    storage: dict = Field(default_factory=dict)
    logs: dict = Field(default_factory=dict)


class APIResponse(BaseModel):
    """Standard API-Response"""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None
