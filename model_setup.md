# Local Gemma 4 Model Setup

This note records the minimal commands for running the Private Memory Map demo
with local Gemma 4 models through Ollama.

## 1. Install Ollama

On Windows:

```powershell
winget install --id Ollama.Ollama --accept-package-agreements --accept-source-agreements
```

Restart PowerShell if `ollama` is not on `PATH`. In this environment, the
executable was also available at:

```powershell
$env:LOCALAPPDATA\Programs\Ollama\ollama.exe
```

## 2. Use the Project Virtual Environment

All Python commands for this repo should use:

```powershell
.\.venv\Scripts\python
```

Verify the Ollama Python client:

```powershell
.\.venv\Scripts\python -c "import sys, ollama; print(sys.executable); print(sys.prefix)"
```

## 3. Pull Gemma 4 Models

Pull the default model used by the app:

```powershell
ollama pull gemma4:e4b-128k
```

Optional smaller model:

```powershell
ollama pull gemma4:e2b-128k
```

Check installed models:

```powershell
ollama list
```

Expected installed models in this environment:

```text
gemma4:e4b-128k    9.6 GB
gemma4:e2b-128k    7.2 GB
gemma4:e4b         9.6 GB
gemma4:e2b         7.2 GB
```

## 4. Smoke Test the App Workflow

Run a real local workflow against one image:

```powershell
.\.venv\Scripts\python scripts\smoke_test_real_workflow.py C:\path\to\travel-photo.jpg
```

This calls Gemma for photo analysis, trip synthesis, and one grounded Q&A
response. It is intentionally separate from automated tests because local model
runtime depends on hardware.

## Notes

- The Python `ollama` package is only the client library. Ollama itself must be
  installed and serving locally.
- `gemma4:e4b-128k` is the default configured model.
- If downloads are unreliable, limiting transfer concurrency can help:

```powershell
[Environment]::SetEnvironmentVariable("OLLAMA_MAX_TRANSFER_STREAMS", "1", "User")
$env:OLLAMA_MAX_TRANSFER_STREAMS = "1"
```
