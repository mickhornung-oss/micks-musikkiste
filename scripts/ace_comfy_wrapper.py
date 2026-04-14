"""
ACE-Step wrapper for ComfyUI Desktop (local API).

This script emulates the CLI contract expected by Micks Musikkiste:
  python scripts/ace_comfy_wrapper.py --output <path> --duration <sec> --tags <csv> [...]

Instead of calling a native ACE-Step binary it converts a ComfyUI workflow export
into the backend prompt format expected by /prompt and then downloads the produced
audio file from ComfyUI history.
"""

import argparse
import json
import random
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path


def http_json(url: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get_bytes(url: str):
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read()


def poll_history(base_url: str, prompt_id: str, timeout: int = 1800, interval: float = 5.0):
    end = time.time() + timeout
    url = f"{base_url}/history/{prompt_id}"
    while time.time() < end:
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                history = json.loads(resp.read().decode("utf-8"))
        except Exception:
            time.sleep(interval)
            continue

        entry = history.get(prompt_id, {})
        status = entry.get("status", {})
        if status.get("completed"):
            return entry
        if status.get("status_str") == "error" or status.get("failed"):
            raise RuntimeError(f"ComfyUI job failed: {status}")
        time.sleep(interval)
    raise TimeoutError("ComfyUI job did not complete in time")


def pick_first_audio(entry: dict) -> tuple[str, str, str]:
    outputs = entry.get("outputs", {})
    candidates = []
    for node_outputs in outputs.values():
        if isinstance(node_outputs, dict):
            audio_items = node_outputs.get("audio") or []
            for file_info in audio_items:
                if isinstance(file_info, dict) and file_info.get("filename"):
                    candidates.append(
                        (
                            0 if file_info.get("type") == "output" else 1,
                            file_info["filename"],
                            file_info.get("subfolder", ""),
                            file_info.get("type", "output"),
                        )
                    )
        elif isinstance(node_outputs, list):
            for file_info in node_outputs:
                if isinstance(file_info, dict) and file_info.get("type") == "audio":
                    candidates.append(
                        (
                            1,
                            file_info["filename"],
                            file_info.get("subfolder", ""),
                            file_info.get("type", "output"),
                        )
                    )

    if candidates:
        _, filename, subfolder, file_type = sorted(candidates, key=lambda item: item[0])[0]
        return (
            filename,
            subfolder,
            file_type,
        )

    raise RuntimeError("No audio file found in ComfyUI history response")


def build_output_prefix(output_path: Path) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", output_path.stem).strip("._-")
    if not stem:
        stem = "micks_track"
    return f"audio/{stem}"


def convert_workflow_to_prompt(workflow: dict) -> dict:
    links_by_id = {}
    for link in workflow.get("links", []):
        if isinstance(link, list) and len(link) >= 6:
            links_by_id[link[0]] = link

    prompt = {}
    for node in workflow.get("nodes", []):
        node_id = str(node["id"])
        widget_values = list(node.get("widgets_values") or [])
        widget_index = 0
        inputs = {}

        for input_def in node.get("inputs", []):
            input_name = input_def.get("name")
            if not input_name:
                continue

            link_id = input_def.get("link")
            if isinstance(link_id, int):
                link = links_by_id.get(link_id)
                if link is None:
                    raise KeyError(f"Workflow link {link_id} not found for node {node_id}")
                inputs[input_name] = [str(link[1]), int(link[2])]
                continue

            if input_def.get("widget") is not None and widget_index < len(widget_values):
                inputs[input_name] = widget_values[widget_index]
                widget_index += 1

        prompt[node_id] = {
            "class_type": node["type"],
            "inputs": inputs,
        }

    return prompt


def apply_ace_overrides(
    prompt: dict,
    duration: int,
    title: str,
    tags: str,
    lyrics: str,
    negative_prompts: str,
    instrumental: bool,
    output_path: Path,
):
    output_prefix = build_output_prefix(output_path)
    saw_audio_output = False
    for node in prompt.values():
        class_type = node.get("class_type")
        if class_type == "ACEModelLoader":
            inputs = node.setdefault("inputs", {})
            inputs["cpu_offload"] = True
            inputs["torch_compile"] = False
            continue

        if class_type == "ACEStepGen":
            inputs = node.setdefault("inputs", {})
            inputs["prompt"] = build_prompt_text(title, tags)
            inputs["lyrics"] = build_lyrics_text(title, lyrics, instrumental)
            inputs["parameters"] = build_default_parameters(duration)
            inputs["delicious_song"] = "None"
            inputs["negative_prompt"] = build_negative_prompt_text(
                inputs.get("negative_prompt"),
                negative_prompts,
                instrumental,
            )
            continue

        if class_type == "PreviewAudio":
            audio_input = node.get("inputs", {}).get("audio")
            node["class_type"] = "SaveAudioMP3"
            node["inputs"] = {
                "audio": audio_input,
                "filename_prefix": output_prefix,
                "quality": "320k",
            }
            saw_audio_output = True
            continue

        if class_type in {"SaveAudio", "SaveAudioMP3", "SaveAudioOpus"}:
            inputs = node.setdefault("inputs", {})
            inputs["filename_prefix"] = output_prefix
            if class_type == "SaveAudioMP3":
                inputs["quality"] = "320k"
            saw_audio_output = True

    if not saw_audio_output:
        raise RuntimeError("Workflow does not contain a PreviewAudio/SaveAudio output node")


def build_default_parameters(duration: int) -> str:
    params = {
        "audio_duration": max(5, int(duration)),
        "infer_step": 8,
        "guidance_scale": 15,
        "scheduler_type": "euler",
        "cfg_type": "apg",
        "omega_scale": 10,
        "guidance_interval": 0.65,
        "guidance_interval_decay": 0.0,
        "min_guidance_scale": 3,
        "use_erg_tag": True,
        "use_erg_lyric": False,
        "use_erg_diffusion": True,
        "oss_steps": "",
        "guidance_scale_text": 0.0,
        "guidance_scale_lyric": 0.0,
        "manual_seeds": random.randint(1, 2**31 - 1),
    }
    return repr(params)


def build_prompt_text(title: str, tags: str) -> str:
    parts = []
    if title.strip():
        parts.append(title.strip())
    if tags.strip():
        parts.extend(chunk.strip() for chunk in tags.split(",") if chunk.strip())
    if not parts:
        parts = ["Techno", "Hip-Hop", "electronic beat", "modern production"]
    return ", ".join(parts)


def build_negative_prompt_text(existing: str, negative_prompts: str, instrumental: bool) -> str:
    parts = []
    if existing and str(existing).strip():
        parts.append(str(existing).strip())
    if negative_prompts.strip():
        parts.extend(chunk.strip() for chunk in negative_prompts.split(",") if chunk.strip())
    parts.extend(["Noise", "roar", "harshness"])
    if instrumental:
        parts.extend(["lead vocals", "spoken word", "rap vocals", "singing"])

    deduped = []
    for part in parts:
        if part not in deduped:
            deduped.append(part)
    return ", ".join(deduped)


def build_lyrics_text(title: str, lyrics: str, instrumental: bool) -> str:
    if lyrics.strip():
        return lyrics.strip()
    if instrumental:
        return "[instrumental]\nno vocals\nfocus on groove and arrangement"
    seed_text = title.strip() or "Micks Musikkiste"
    return f"[verse]\n{seed_text}\n{seed_text}\n\n[chorus]\n{seed_text}\n{seed_text}"


def run(
    comfy_url: str,
    workflow_path: Path,
    output_path: Path,
    duration: int,
    title: str,
    tags: str,
    lyrics: str,
    negative_prompts: str,
    instrumental: bool,
):
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    prompt = convert_workflow_to_prompt(workflow)
    apply_ace_overrides(prompt, duration, title, tags, lyrics, negative_prompts, instrumental, output_path)

    prompt_resp = http_json(
        f"{comfy_url}/prompt",
        {"prompt": prompt, "extra_data": {"source": "micks-musikkiste"}},
    )
    prompt_id = prompt_resp.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"No prompt_id returned: {prompt_resp}")

    entry = poll_history(comfy_url, prompt_id)
    filename, subfolder, file_type = pick_first_audio(entry)
    params = urllib.parse.urlencode(
        {"filename": filename, "subfolder": subfolder, "type": file_type}
    )
    file_bytes = http_get_bytes(f"{comfy_url}/view?{params}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(file_bytes)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Target file path")
    parser.add_argument("--duration", default="20", help="Requested duration in seconds")
    parser.add_argument("--tags", default="", help="Comma-separated prompt tags")
    parser.add_argument("--lyrics", default="", help="Lyrics text")
    parser.add_argument("--title", default="", help="Track title")
    parser.add_argument("--negative-prompts", default="", help="Comma-separated negative prompt tags")
    parser.add_argument("--instrumental", action="store_true", help="Prefer instrumental output without vocals")
    parser.add_argument(
        "--workflow",
        required=True,
        help="Path to the ACE-Step workflow export JSON",
    )
    parser.add_argument(
        "--comfy-url",
        default="http://127.0.0.1:8188",
        help="Base URL of the local ComfyUI API",
    )
    args = parser.parse_args()

    comfy_url = args.comfy_url.rstrip("/")
    workflow_path = Path(args.workflow)
    output_path = Path(args.output)

    if not workflow_path.exists():
        raise FileNotFoundError(f"Workflow not found: {workflow_path}")

    run(
        comfy_url,
        workflow_path,
        output_path,
        int(args.duration),
        args.title,
        args.tags,
        args.lyrics,
        args.negative_prompts,
        args.instrumental,
    )


if __name__ == "__main__":
    main()
