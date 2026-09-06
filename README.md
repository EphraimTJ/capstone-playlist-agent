# Natural-Language Playlist-Builder Agent

A capstone baseline for an agentic AI system. You describe a vibe in plain
English — *"a 10-song high-energy pop playlist from the 2010s for a workout"* —
and the agent inspects a real Spotify dataset of ~33k tracks, writes and runs
pandas code to filter it by audio features (genre, release era, energy,
danceability, tempo, valence, popularity, …), and returns a playlist of real
tracks that match the request.

It is a **tool-use / agentic-loop** baseline: one `run_pandas` tool, a bounded
reasoning loop, and an OpenAI-compatible LLM (runs on Groq's free tier).

## Quick start

```bash
py -3.13 -m pip install -r requirements.txt

# PowerShell (Groq free tier — get a key at https://console.groq.com/keys)
$env:OPENAI_API_KEY  = "gsk_your_groq_key_here"
$env:OPENAI_BASE_URL = "https://api.groq.com/openai/v1"

py -3.13 run_baseline.py --input examples/test1.txt --model openai/gpt-oss-120b
```

Full setup (Command Prompt / bash variants, OpenAI instead of Groq, etc.) is in
[`examples/readme.md`](examples/readme.md).

## What's here

| Path | What it is |
|------|------------|
| `run_baseline.py` | The agent: loads data, runs the tool-use loop, prints & saves the playlist |
| `examples/spotify_songs.csv` | Dataset (~33k tracks, TidyTuesday mirror; auto-downloaded if missing) |
| `examples/test1.txt`, `examples/test2.txt` | Example playlist requests |
| `examples/readme.md` | Configuration & run guide |
| `outputs/` | Generated playlists and terminal screenshots |
| `Capstone_Proposal.docx` | The written project proposal |
| `requirements.txt` | Python dependencies (`openai`, `pandas`) |

## Dataset

Spotify tracks from the [TidyTuesday](https://github.com/rfordatascience/tidytuesday/tree/master/data/2020/2020-01-21)
project (2020-01-21), mirrored on GitHub as a plain CSV — no Kaggle account or
API token required.
