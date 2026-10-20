import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


APP_DIR = Path(__file__).parent
HOST = "127.0.0.1"
PORT = 8000
MAX_REQUEST_SIZE = 16384
MODEL = "gemini-2.5-flash"
CHARACTERS = {
    "Rama",
    "Sita",
    "Hanuman",
    "Lakshmana",
    "Bharata",
    "Shatrughna",
    "Dasharatha",
    "Kaushalya",
    "Kaikeyi",
    "Sumitra",
    "Ravana",
    "Vibhishana",
    "Kumbhakarna",
    "Indrajit (Meghanada)",
    "Jatayu",
    "Sugriva",
    "Vali",
    "Angada",
    "Jambavan",
    "Nala",
    "Nila",
    "Shabari",
    "Ahalya",
    "Janaka",
    "Mandodari",
    "Surpanakha",
    "Maricha",
    "Tara",
    "Urmila",
}
SETTINGS = {"The forest", "Lanka", "Ayodhya"}
LESSONS = {
    "Courage and doing what is right",
    "Devotion and friendship",
    "Wisdom and patience",
    "Hope and perseverance",
}
LENGTHS = {"Short", "Medium", "Long", "Very long"}
LENGTH_WORDS = {
    "Short": ("about 150 words", 700),
    "Medium": ("about 350 words", 1200),
    "Long": ("about 800 words", 2400),
    "Very long": ("about 1,500 words", 4200),
}


class StoryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in {"/", "/index.html"}:
            self.send_json(404, {"error": "Page not found."})
            return

        try:
            page = (APP_DIR / "index.html").read_bytes()
        except OSError:
            self.send_json(500, {"error": "The app page could not be loaded."})
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self):
        if self.path != "/api/story":
            self.send_json(404, {"error": "API endpoint not found."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.send_json(400, {"error": "A valid request body is required."})
            return

        if content_length <= 0 or content_length > MAX_REQUEST_SIZE:
            self.send_json(400, {"error": "The request body is empty or too large."})
            return

        try:
            data = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json(400, {"error": "The request body must be valid JSON."})
            return

        if not isinstance(data, dict):
            self.send_json(400, {"error": "The request body must be a JSON object."})
            return

        choices = {
            "setting": (data.get("setting"), SETTINGS),
            "lesson": (data.get("lesson"), LESSONS),
            "length": (data.get("length"), LENGTHS),
        }
        language = data.get("language")
        if not isinstance(language, str) or not language.strip() or len(language) > 80:
            self.send_json(400, {"error": "Enter a valid story language (up to 80 characters)."})
            return

        characters = data.get("characters")
        if (
            not isinstance(characters, list)
            or not characters
            or len(characters) > len(CHARACTERS)
            or any(not isinstance(character, str) or character not in CHARACTERS
                   for character in characters)
            or len(set(characters)) != len(characters)
        ):
            self.send_json(400, {"error": "Choose one or more valid characters."})
            return
        if any(
            not isinstance(value, str) or value not in allowed
            for value, allowed in choices.values()
        ):
            self.send_json(400, {"error": "Please select valid story options."})
            return

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            self.send_json(
                503,
                {
                    "error": (
                        "Gemini is not configured. Set the GEMINI_API_KEY "
                        "environment variable, then restart the app."
                    )
                },
            )
            return

        size, max_output_tokens = LENGTH_WORDS[data["length"]]
        character_list = ", ".join(characters)
        prompt = (
            "Write an original, family-friendly Dussehra story inspired by the "
            "Ramayana. Treat the tradition and its characters respectfully. "
            "Do not present the story as scripture or claim it is an authentic "
            "traditional verse. Use clear, engaging language for a general "
            "audience. Give it a short title, then the story, and finish with "
            "one sentence about its lesson. Write the entire story, including "
            f"its title and lesson, in {language.strip()}. "
            "Invent a fresh plot; avoid repeating the same story, beginning, "
            "conflict, or resolution. Use this creative variation seed: "
            f"{secrets.token_hex(8)}. "
            f"Feature these characters, giving each a meaningful role: {character_list}. "
            f"Setting: {data['setting']}. "
            f"Lesson: {data['lesson']}. "
            f"Length: {size}."
        )
        request_body = json.dumps(
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.8,
                    "maxOutputTokens": max_output_tokens,
                },
            }
        ).encode("utf-8")
        request = Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=45) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            self.send_json(502, {"error": self.upstream_error(error)})
            return
        except (URLError, TimeoutError):
            self.send_json(
                502,
                {"error": "Could not reach Gemini. Check your connection and try again."},
            )
            return
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json(502, {"error": "Gemini returned an unreadable response."})
            return

        try:
            story = result["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError, AttributeError):
            self.send_json(
                502,
                {"error": "Gemini did not return a story. Please try again."},
            )
            return

        if not story:
            self.send_json(502, {"error": "Gemini returned an empty story. Please try again."})
            return

        self.send_json(200, {"story": story})

    @staticmethod
    def upstream_error(error):
        raw_body = error.read().decode("utf-8", errors="replace").strip()
        try:
            details = json.loads(raw_body)
            message = details["error"]["message"]
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError):
            message = ""

        if message:
            return f"Gemini could not generate a story: {message}"
        if error.code in {401, 403}:
            return (
                "Gemini denied the request. Check that GEMINI_API_KEY is valid, "
                "the Gemini API is enabled for its project, and the key allows this API."
            )
        if error.code == 429:
            return "Gemini's request quota was reached. Check the API project's quota and try again."
        return f"Gemini could not generate a story (HTTP {error.code})."

    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), StoryHandler)
    print(f"Dussehra Story Generator is running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()
