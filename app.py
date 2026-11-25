
from pathlib import Path
from flask import Flask, render_template, abort, send_from_directory

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
TANKS_DIR = BASE_DIR / "tanks"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


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
                "image": image.name,
                "description": description
            })

        generations.append({
            "name": generation_folder.name,
            "folder": generation_folder.name,
            "tanks": tanks
        })

    return generations


def get_generation(generation_name):
    for generation in load_tanks():
        if generation["folder"] == generation_name:
            return generation

    return None


def get_tank(generation_name, tank_name):
    generation = get_generation(generation_name)

    if not generation:
        return None, None

    for tank in generation["tanks"]:
        if tank["folder"] == tank_name:
            return generation, tank

    return generation, None


@app.route("/")
def index():
    generations = load_tanks()

    return render_template(
        "index.html",
        generations=generations
    )


@app.route("/catalog/<generation_name>")
def catalog(generation_name):
    generation = get_generation(generation_name)

    if not generation:
        abort(404)

    return render_template(
        "catalog.html",
        generation=generation
    )


@app.route("/tank/<generation_name>/<tank_name>")
def tank_page(generation_name, tank_name):
    generation, tank = get_tank(
        generation_name,
        tank_name
    )

    if not tank:
        abort(404)

    return render_template(
        "tank.html",
        generation=generation,
        tank=tank
    )


@app.route("/tank_image/<generation_name>/<tank_name>/<image_name>")
def tank_image(generation_name, tank_name, image_name):
    folder = TANKS_DIR / generation_name / tank_name

    if not folder.exists():
        abort(404)

    # Проверяем, что файл действительно находится в папке танка
    if image_name not in [file.name for file in folder.iterdir()]:
        abort(404)

    return send_from_directory(folder, image_name)


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=False)
