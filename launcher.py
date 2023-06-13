# Run this script for first time setups

import json
import os
import sqlite3

try:
    os.mkdir("db")
except FileExistsError:
    pass

# jsons
jsons = {
    "self_roles": {},
}

for json_name, content in jsons.items():
    try:
        with open(f"db/{json_name}.json", "r") as file:
            json.load(file)
    except FileNotFoundError:
        with open(f"db/{json_name}.json", "w") as file:
            json.dump(content, file)

# SQLite db
for name in ("self_roles",):
    conn = sqlite3.connect(f"db/{name}.db")
    c = conn.cursor()

    with open(f"utils/schemas/{name}.sql") as sql:
        c.executescript(sql.read())
        conn.commit()
