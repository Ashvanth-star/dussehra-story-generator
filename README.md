# Dussehra Story Generator

A small web app that creates family-friendly stories inspired by the Ramayana. Choose characters, a setting, a lesson, four story lengths, and a story language. The Ramayana has many versions and traditions, so the character list is a selection rather than an exhaustive count. The offline generator selects from different original story plots and avoids using the same plot twice in a row during the browser session.

## Open without installing anything

Open `index.html` in a browser or publish it as a static site (for example, with GitHub Pages). English stories are generated in the browser and do not need Python or an API key. For other languages, the app sends the generated story text to Google's online translation service, so an internet connection is required. The language field includes suggestions and also accepts language names or 2–3 letter language codes; availability depends on the translation service.

The Python/Gemini mode is for running the app locally at `http://127.0.0.1:8000`; it is not required for the static website.

## Optional Gemini API mode

The Python server can use Gemini to generate stories in the requested language. Its API key is read only by the local server; it is not included in the page or sent to the browser. Supported languages depend on Gemini's language capabilities.

## Requirements

- Python 3.9 or newer
- A Gemini API key

## Run on Windows

In PowerShell, from this folder:

```powershell
$env:GEMINI_API_KEY = "your-api-key"
python app.py
```

Open <http://127.0.0.1:8000>. Press `Ctrl+C` in the terminal to stop the server.

The key is held in the environment for that PowerShell session only. The app makes a Gemini API request each time you generate a story. Gemini authorization failures are shown as a readable message. If access is denied, verify the API key, that the Gemini API is enabled for its project, and that the key permits this API.
