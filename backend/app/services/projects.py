"""Project-Management Service"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from app.config import settings


class ProjectService:
    """Service für lokale Projekte"""
    
    @staticmethod
    def create_project(
        name: str,
        project_type: str,
        genre: str,
        mood: str,
        duration: int,
        parameters: dict,
        output_file: Optional[str] = None,
        metadata: Optional[dict] = None,
        preset_used: Optional[str] = None,
        lyrics: Optional[str] = None,
        negative_prompts: Optional[list] = None
    ) -> dict:
        """Erstelle neues Projekt"""
        project_id = str(uuid.uuid4())[:8]
        
        project_data = {
            "id": project_id,
            "name": name,
            "type": project_type,
            "genre": genre,
            "mood": mood,
            "duration": duration,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "data_file": str(settings.PROJECTS_DIR / f"{project_id}.json"),
            "output_file": output_file,
            "parameters": parameters,
            "metadata": metadata or {},
            "preset_used": preset_used,
            "lyrics": lyrics,
            "negative_prompts": negative_prompts or [],
            "exports": [],
            "last_export_at": None
        }
        
        # Speichere als JSON
        project_file = settings.PROJECTS_DIR / f"{project_id}.json"
        project_file.write_text(json.dumps(project_data, indent=2, ensure_ascii=False))
        
        return project_data
    
    @staticmethod
    def get_project(project_id: str) -> Optional[dict]:
        """Lade Projekt"""
        project_file = settings.PROJECTS_DIR / f"{project_id}.json"
        
        if not project_file.exists():
            return None
        
        try:
            return json.loads(project_file.read_text())
        except Exception:
            return None
    
    @staticmethod
    def list_projects() -> List[dict]:
        """Auflisten aller Projekte"""
        projects = []
        
        for json_file in settings.PROJECTS_DIR.glob("*.json"):
            try:
                data = json.loads(json_file.read_text())
                projects.append(data)
            except Exception:
                continue
        
        # Sortiere nach Erstellungszeit (neueste zuerst)
        projects.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        return projects
    
    @staticmethod
    def delete_project(project_id: str) -> bool:
        """Lösche Projekt"""
        project_file = settings.PROJECTS_DIR / f"{project_id}.json"
        
        if project_file.exists():
            project_file.unlink()
            return True
        
        return False
    
    @staticmethod
    def save_project_metadata(project_id: str, metadata: dict) -> bool:
        """Update Projekt-Metadaten"""
        project_file = settings.PROJECTS_DIR / f"{project_id}.json"
        
        if not project_file.exists():
            return False
        
        try:
            project_data = json.loads(project_file.read_text())
            project_data["metadata"].update(metadata)
            project_data["updated_at"] = datetime.now().isoformat()
            project_file.write_text(json.dumps(project_data, indent=2, ensure_ascii=False))
            return True
        except Exception:
            return False

    @staticmethod
    def add_export(project_id: str, filename: str, path: str) -> Optional[dict]:
        """Protokolliert einen Export für ein Projekt"""
        project_file = settings.PROJECTS_DIR / f"{project_id}.json"
        
        if not project_file.exists():
            return None
        
        try:
            project_data = json.loads(project_file.read_text())
            export_record = {
                "filename": filename,
                "path": path,
                "exported_at": datetime.now().isoformat()
            }
            project_data.setdefault("exports", []).append(export_record)
            project_data["last_export_at"] = export_record["exported_at"]
            project_data["updated_at"] = export_record["exported_at"]
            project_file.write_text(json.dumps(project_data, indent=2, ensure_ascii=False))
            return project_data
        except Exception:
            return None


# Globale Service-Instanz
project_service = ProjectService()
