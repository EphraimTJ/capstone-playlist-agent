# Configuration & Run Guide

Configuration location for the **NL Playlist-Builder Agent** baseline.

## 1. Install dependencies

Requires Python 3.10+ (developed on 3.13).

```bash
py -3.13 -m pip install -r requirements.txt
```

## 2. Configure the model provider

The baseline uses an **OpenAI-compatible** API. It works with OpenAI, or any
compatible endpoint (Groq, OpenRouter, etc.) by setting two environment
variables. The reference configuration uses **Groq's free tier**.

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY  = "gsk_your_groq_key_here"
$env:OPENAI_BASE_URL = "https://api.groq.com/openai/v1"
```

**Windows (Command Prompt / cmd.exe)** — use `set`, and **do not quote** the value:
```bat
set OPENAI_API_KEY=gsk_your_groq_key_here
set OPENAI_BASE_URL=https://api.groq.com/openai/v1
```

**macOS / Linux (bash):**
```bash
export OPENAI_API_KEY="gsk_your_groq_key_here"
export OPENAI_BASE_URL="https://api.groq.com/openai/v1"
```

- Get a free Groq key at https://console.groq.com/keys (no credit card).
- The `$env:` syntax is PowerShell-only; in Command Prompt it errors with
  "The filename, directory name, or volume label syntax is incorrect." Use the
  `set` form above instead (and note cmd includes quotes in the value, so omit them).
- These variables last only for the current terminal window. Set them again in
  each new window, or run all commands in the same session.
- To use **OpenAI instead**, set only `OPENAI_API_KEY` (leave `OPENAI_BASE_URL`
  unset) and pass `--model gpt-4o-mini`.

## 3. Dataset

Real Spotify dataset (~33k tracks) from the TidyTuesday project on GitHub:
`https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2020/2020-01-21/spotify_songs.csv`

It is committed at `examples/spotify_songs.csv`. If that file is missing, the
script **auto-downloads it on first run** — no Kaggle account or API token needed.

## 4. Run the baseline

```bash
py -3.13 run_baseline.py --input examples/test1.txt
py -3.13 run_baseline.py --input examples/test2.txt
```

The default model is `qwen/qwen3.8-27b` on Groq — a light model with generous
free-tier limits that handles tool calls reliably, so no `--model` flag is
needed. Pass `--model` only to override it.

| Flag       | Meaning                                   | Default                      |
|------------|-------------------------------------------|------------------------------|
| `--input`  | Text file containing the playlist request | (required)                   |
| `--data`   | CSV dataset                               | `examples/spotify_songs.csv` |
| `--model`  | Model name                                | `qwen/qwen3.8-27b`           |

## 5. Where things live

- **Requests (inputs):** `examples/test1.txt`, `examples/test2.txt`
- **Dataset:** `examples/spotify_songs.csv`
- **Playlists written to:** `outputs/<input-name>.out.txt`

## Known setup limitations

- The chosen model must support tool (function) calling. On Groq's free tier,
  `qwen/qwen3.8-27b` (default) and `openai/gpt-oss-120b` both work well. The
  smaller `openai/gpt-oss-20b` is not recommended: it often returns malformed
  tool-call arguments (`tool_use_failed`).
- Groq's free tier limits output tokens per minute (as low as 1000 for the
  default model). The baseline caps output at `--max-tokens 900` per call and
  automatically retries after a short wait if it still hits a 429, so runs
  usually recover on their own. If you keep hitting limits, wait a minute and
  run again, or pass a smaller `--max-tokens`.
