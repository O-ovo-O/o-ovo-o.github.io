#! /usr/bin/python3

import argparse
import os
import sys
import shutil
import json
import html

try:
    from jsonschema import validate, ValidationError
    from PIL import Image
except ImportError:
    print("zainstaluj sobie jsonschema i pil", file=sys.stderr)
    sys.exit(1)


SCHEMA_V1 = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "tags": {"type": "string"},
        "user": {"type": "string"},
        "price": {"type": "number"},
        "desc": {"type": "string"},
        "foto": {"type": "string"},
    },
    "required": ["name", "tags", "user", "price"],
}
HTML_V1 = """<!DOCTYPE html>
<html lang="pl"><head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
    <h1>co: {title}</h1>
    <h2>kto: {user}</h2>
    <p>ile: {price}</p>
    <p>opis: {content}</p>
    <p>foto: {foto}</p>
</body>
</html>
"""

SCHEMA = SCHEMA_V1
HTML = HTML_V1
TABLE = "./data/table.md"


def add_row_to_md_tab(entry):
    with open(TABLE, "r") as _file:
        lines = _file.readlines()

    where, user, users = 0, 0, 0
    for i, line in enumerate(lines):
        if line.startswith("|"):
            where += 1
        if line.startswith("[u"):
            users += 1
            if entry["user"] in line:
                user = int(line[2:].split("]:")[0])
    if not user:
        usr = f"[{entry['user']}][u{users + 1}]"
    else:
        usr = f"[{entry['user']}][u{user}]"

    link = f"[link][a{where - 1}]"

    new_row = [entry["name"], entry["tags"], usr, link, f"{entry['price']:.2f}"]

    lines.insert(where, "| " + " | ".join(new_row) + " |\n")
    if not user:
        lines.insert(
            where + 1 + users + 2,
            f"[u{users + 1}]: https://wykop.pl/ludzie/{entry['user']}\n",
        )
    lines.insert(
        len(lines) - 1,
        f"[a{where - 1}]: https://o-ovo-o.github.io/ogloszonka/data/data/{where - 1}/{where - 1}.html\n",
    )

    with open(TABLE, "w") as _file:
        _file.writelines(lines)

    return where - 1


def make_crude_html(where, entry):
    dst = f"./data/data/{where}"
    os.makedirs(dst, exist_ok=True)
    if foto := entry.get("foto", None):
        try:
            with Image.open(foto) as img:
                if img.format != "PNG":
                    raise RuntimeError("to nie jest png")
            if os.path.getsize(foto) > 200 * 1024:
                raise RuntimeError("foto jest za duze, 200kB max")
            shutil.copy(foto, dst)
            foto = (
                '<img src="'
                + html.escape(os.path.basename(foto))
                + '" alt="miał być obrazek" width="500" height="500">'
            )
        except (PermissionError, OSError, FileNotFoundError, RuntimeError) as err:
            print(f"popsules -> {err}", file=sys.stderr)
            foto = "użyszkodnik zepsuł, nima foto"
    else:
        foto = "brak foto"

    with open(f"{dst}/{where}.html", "w") as _file:
        _file.write(
            HTML.format(
                user=html.escape(entry["user"]),
                title=html.escape(entry["name"]),
                price=entry["price"],
                content=html.escape(entry.get("desc", "brak opisu")),
                foto=foto,
            )
        )


def main():
    parser = argparse.ArgumentParser(description="dodaj se do tabelki")
    parser.add_argument("number", type=int, help="numer ogloszonka")
    args = parser.parse_args()

    file_path = f"./data/data/{args.number}.json"
    if not os.path.exists(file_path):
        print(f"no such file/dir: {file_path}")
        return

    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            validate(instance=data, schema=SCHEMA)
            where = add_row_to_md_tab(data)
            make_crude_html(where, data)
    except json.JSONDecodeError:
        print("bad JSON")
    except ValidationError as e:
        print(f"JSON - schema: {e.message}")


if __name__ == "__main__":
    main()
