"""Runnable baseline: a natural-language playlist-builder agent.

The user describes a vibe in plain English ("upbeat 2010s pop for a
workout"). The agent inspects a real Spotify dataset of ~33k tracks,
writes pandas code to filter it by audio features (genre, release year,
energy, danceability, tempo, valence, popularity, ...), and returns a
playlist of tracks that satisfy the request.

This is a tool-use / agentic-loop baseline built on the OpenAI Chat
Completions API with function calling. It is intentionally minimal: one
tool (run_pandas), a bounded loop, no external Spotify API, no learned
recommender.

Dataset: TidyTuesday `spotify_songs.csv` (~33k rows), auto-downloaded
from GitHub on first run if not present locally.

Usage:
    py -3.13 run_baseline.py --input examples/test1.txt
    py -3.13 run_baseline.py --input examples/test2.txt --data examples/spotify_songs.csv
"""
import argparse
import contextlib
import io
import json
import os
import sys
import urllib.request

import pandas as pd

try:
    from openai import OpenAI
except ImportError:
    sys.exit("openai package not installed. Run: py -3.13 -m pip install -r requirements.txt")

DATA_URL = (
    "https://raw.githubusercontent.com/rfordatascience/tidytuesday/"
    "master/data/2020/2020-01-21/spotify_songs.csv"
)
MAX_STEPS = 12  # safety bound on the tool-use loop

RUN_PANDAS_TOOL = {
    "type": "function",
    "function": {
        "name": "run_pandas",
        "description": (
            "Execute a snippet of Python/pandas code against the loaded "
            "DataFrame `df` of Spotify tracks. Anything printed with print() is "
            "returned to you. Use this to inspect the data and select tracks."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code. `df` and `pd` are defined. print() what you want to see.",
                }
            },
            "required": ["code"],
        },
    },
}


def ensure_dataset(path: str) -> None:
    """Download the Spotify dataset from GitHub if it is not present locally."""
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    print(f"Dataset not found locally — downloading from GitHub...\n  {DATA_URL}")
    urllib.request.urlretrieve(DATA_URL, path)
    print(f"Saved dataset to {path}\n")


def run_pandas(code: str, df: pd.DataFrame) -> str:
    """Execute `code` with `df` in scope, capturing stdout. Sandbox is minimal
    by design (baseline); errors are returned as text so the model can retry."""
    buffer = io.StringIO()
    namespace = {"df": df, "pd": pd}
    try:
        with contextlib.redirect_stdout(buffer):
            exec(code, namespace)  # noqa: S102 - intentional for the baseline
    except Exception as exc:  # noqa: BLE001 - surface errors back to the model
        return f"ERROR: {type(exc).__name__}: {exc}"
    out = buffer.getvalue().strip()
    return out if out else "(no output — remember to print() your result)"


def build_system_prompt(df: pd.DataFrame) -> str:
    schema = ", ".join(f"{c} ({t})" for c, t in df.dtypes.astype(str).items())
    return (
        "You are a music playlist-builder agent. Build a playlist of real tracks "
        "that matches the user's request, selected from a pandas DataFrame `df` of "
        "Spotify tracks.\n"
        f"Columns: {schema}\n"
        f"Rows: {len(df)}\n\n"
        "Notes on the data:\n"
        "- Audio features danceability, energy, valence (musical positivity/mood), "
        "acousticness, speechiness, instrumentalness, liveness are floats in [0,1]; "
        "tempo is BPM; track_popularity is 0-100; playlist_genre is one of "
        "pop/rap/rock/latin/r&b/edm.\n"
        "- Release year can be parsed from the first 4 characters of "
        "track_album_release_date.\n"
        "- The dataset contains duplicate tracks (the same song in several "
        "playlists); de-duplicate on track_name + track_artist before returning.\n\n"
        "Use the run_pandas tool to filter and select tracks — never invent songs. "
        "Be decisive: do not repeat the same query, and as soon as you have enough "
        "matching tracks, stop calling the tool and write the final playlist. "
        "Honour the requested number of songs (default 10 if unspecified). When done, "
        "reply with (1) a one-line summary of the filters you applied, then (2) a "
        "numbered playlist where each line is: Title - Artist (genre, year, key features)."
    )


def build_playlist(request: str, df: pd.DataFrame, model: str) -> str:
    client = make_client()
    messages = [
        {"role": "system", "content": build_system_prompt(df)},
        {"role": "user", "content": request},
    ]
    for step in range(1, MAX_STEPS + 1):
        response = client.chat.completions.create(
            model=model, messages=messages, tools=[RUN_PANDAS_TOOL]
        )
        msg = response.choices[0].message
        messages.append(msg)
        if not msg.tool_calls:
            return (msg.content or "").strip()
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            code = args.get("code", "")
            first = code.strip().splitlines()[0] if code.strip() else "(empty)"
            more = " ..." if len(code.strip().splitlines()) > 1 else ""
            print(f"  [step {step}] agent ran pandas:  {first}{more}", file=sys.stderr)
            result = run_pandas(code, df)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return "(stopped: reached the maximum number of reasoning steps)"


def make_client() -> "OpenAI":
    """OpenAI-compatible client. Works with OpenAI, Groq, OpenRouter, etc. by
    pointing OPENAI_BASE_URL at the provider's endpoint."""
    base_url = os.environ.get("OPENAI_BASE_URL")  # e.g. https://api.groq.com/openai/v1
    kwargs = {"base_url": base_url} if base_url else {}
    return OpenAI(**kwargs)  # api key read from OPENAI_API_KEY


def main() -> None:
    parser = argparse.ArgumentParser(description="NL playlist-builder agent (baseline).")
    parser.add_argument("--input", required=True, help="Text file containing the playlist request.")
    parser.add_argument("--data", default="examples/spotify_songs.csv", help="CSV dataset path.")
    parser.add_argument("--model", default=os.environ.get("BASELINE_MODEL", "gpt-4o-mini"),
                        help="Model name. Default gpt-4o-mini; for Groq use e.g. "
                             "openai/gpt-oss-120b (or set BASELINE_MODEL).")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is not set. Set it before running the baseline.")

    ensure_dataset(args.data)
    with open(args.input, "r", encoding="utf-8") as f:
        request = f.read().strip()
    df = pd.read_csv(args.data)

    print(f"Request: {request}")
    print(f"Dataset: {args.data} ({len(df):,} tracks)")
    print(f"Model  : {args.model}\n")

    playlist = build_playlist(request, df, args.model)

    print("\n=== PLAYLIST ===")
    print(playlist)

    os.makedirs("outputs", exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.input))[0]
    out_path = os.path.join("outputs", f"{stem}.out.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"Request: {request}\n\nPlaylist:\n{playlist}\n")
    print(f"\nSaved playlist to {out_path}")


if __name__ == "__main__":
    main()
