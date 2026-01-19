import os

from google import genai

import config


GEMINI_MODEL = "gemini-2.5-flash"


def clean_text(text: str) -> str:
    return text.encode("ascii", "replace").decode("ascii")


def _read_env_value(path: str, keys: list[str]) -> str:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                key = key.strip()
                if key not in keys:
                    continue
                value = value.strip().strip("'").strip('"')
                if value:
                    return value
    except FileNotFoundError:
        return ""
    except Exception:
        return ""
    return ""


def _get_api_key() -> str:
    for key_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        value = os.environ.get(key_name)
        if value:
            return value.strip()
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    return _read_env_value(env_path, ["GEMINI_API_KEY", "GOOGLE_API_KEY"])


def _find_latest_test_data_json() -> str:
    base_dir = os.path.join(os.path.dirname(__file__), config.OUTPUT_FOLDER)
    if not os.path.isdir(base_dir):
        raise FileNotFoundError(f"Missing output folder: {base_dir}")
    run_dirs = [
        name for name in os.listdir(base_dir)
        if name.startswith("run_") and os.path.isdir(os.path.join(base_dir, name))
    ]
    for run_name in sorted(run_dirs, reverse=True):
        candidate = os.path.join(base_dir, run_name, "test_data.json")
        if os.path.isfile(candidate):
            return candidate
    fallback = os.path.join(base_dir, "test_data.json")
    if os.path.isfile(fallback):
        return fallback
    raise FileNotFoundError(f"test_data.json not found in {base_dir}")


def main() -> None:
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY.")
    json_path = _find_latest_test_data_json()
    with open(json_path, "r", encoding="utf-8") as handle:
        txt = handle.read()
    prompt = clean_text(txt)

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=(
            "I am providing a JSON format testing report. Extract each module and explain "
            "the errors found. Additionally tell the things to check on. "
            f"The json report is {prompt}"
        ),
    )

    print(response.text)


if __name__ == "__main__":
    main()
