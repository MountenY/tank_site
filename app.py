
from pathlib import Path
from flask import Flask, render_template, abort, send_from_directory
import re

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
TANKS_DIR = BASE_DIR / "tanks"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def slugify(text):
    """Преобразует русское название в латинский URL."""

    translit = {
        "а": "a", "б": "b", "в": "v", "г": "g",
        "д": "d", "е": "e", "ё": "yo", "ж": "zh",
        "з": "z", "и": "i", "й": "y", "к": "k",
        "л": "l", "м": "m", "н": "n", "о": "o",
        "п": "p", "р": "r", "с": "s", "т": "t",
        "у": "u", "ф": "f", "х": "kh", "ц": "ts",
        "ч": "ch", "ш": "sh", "щ": "shch",
        "ъ": "", "ы": "y", "ь": "", "э": "e",
        "ю": "yu", "я": "ya"
    }

    text = text.lower()
    text = "".join(translit.get(char, char) for char in text)
    text = re.sub(r"[^a-z0-9]+", "-", text)

    return text.strip("-")


def load_tanks():
    """Автоматически собирает все танки из папок."""

    generations = []

    if not TANKS_DIR.exists():
        return generations

    generation_folders = sorted(
        [p for p in TANKS_DIR.iterdir() if p.is_dir()],
        key=lambda p: int(p.name.split()[0])
    )

    for generation_folder in generation_folders:
        tanks = []

        tank_folders = sorted(
            [p for p in generation_folder.iterdir() if p.is_dir()],
            key=lambda p: p.name
        )

        for tank_folder in tank_folders:
            images = [
                file for file in tank_folder.iterdir()
                if file.is_file()
                and file.suffix.lower() in IMAGE_EXTENSIONS
            ]

            text_files = [
                file for file in tank_folder.iterdir()
                if file.is_file()
                and file.suffix.lower() == ".txt"
            ]

            if not images:
                continue

            image = images[0]
            description = ""

            if text_files:
                description = text_files[0].read_text(
                    encoding="utf-8"
                ).strip()

            tanks.append({
                "name": tank_folder.name,
                "folder": tank_folder.name,
                "slug": slugify(tank_folder.name),
                "image": image.name,
                "description": description
            })

        generations.append({
            "name": generation_folder.name,
            "folder": generation_folder.name,
            "slug": slugify(generation_folder.name),
            "tanks": tanks
        })

    return generations


def get_generation(generation_slug):
    for generation in load_tanks():
        if generation["slug"] == generation_slug:
            return generation

    return None


def get_tank(generation_slug, tank_slug):
    generation = get_generation(generation_slug)

    if not generation:
        return None, None

    for tank in generation["tanks"]:
        if tank["slug"] == tank_slug:
            return generation, tank

    return generation, None


@app.route("/")
def index():
    generations = load_tanks()

    return render_template(
        "index.html",
        generations=generations
    )


@app.route("/catalog/<generation_slug>")
def catalog(generation_slug):
    generation = get_generation(generation_slug)

    if not generation:
        abort(404)

    return render_template(
        "catalog.html",
        generation=generation
    )


@app.route("/tank/<generation_slug>/<tank_slug>")
def tank_page(generation_slug, tank_slug):
    generation, tank = get_tank(
        generation_slug,
        tank_slug
    )

    if not tank:
        abort(404)

    return render_template(
        "tank.html",
        generation=generation,
        tank=tank
    )


@app.route("/tank_image/<generation_slug>/<tank_slug>/<image_name>")
def tank_image(generation_slug, tank_slug, image_name):
    generation, tank = get_tank(
        generation_slug,
        tank_slug
    )

    if not tank:
        abort(404)

    folder = TANKS_DIR / generation["folder"] / tank["folder"]

    image_path = folder / image_name

    if not image_path.is_file():
        abort(404)

    return send_from_directory(folder, image_name)


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=False)
