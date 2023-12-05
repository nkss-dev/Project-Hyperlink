import asyncpg
import os
import sys
from dataclasses import dataclass

import tabula


@dataclass
class Student:
    roll_number: str
    section: str
    name: str
    email: str
    batch: int
    hostel_id: str
    is_verified: bool


BATCH = int(sys.argv[1])


def parse_roll():
    df = tabula.read_pdf(sys.argv[2], pages="all", multiple_tables=False)[0]

    students: list[Student] = []
    for _, row in df.iterrows():
        try:
            int(row["Unnamed: 0"])
            roll = int(row["Unnamed: 1"])
        except:
            continue

        if isinstance(row["Unnamed: 3"], float):
            *names, section, subsection = row["DATE (DD.MM.YYYY)"].split(" ")
            name = " ".join(names).title()
        else:
            name = row["DATE (DD.MM.YYYY)"].title()
            section, subsection = row["Unnamed: 3"].split(" ")

        # if "repeat" in name.lower():
        #     continue

        if "(" in name:
            name = name.split("(")[0]

        student = Student(
            roll_number=str(roll),
            section=section + str(int(subsection[3:])),
            email=str(roll) + "@nitkkr.ac.in",
            batch=BATCH,
            hostel_id="H0",
            name=name.strip(),
            is_verified=False,
        )
        students.append(student)

    return students


def to_csv(students: list[Student]):
    import pandas as pd

    df = pd.DataFrame(
        data={
            "Roll Number": [s.roll_number for s in students],
            "Name": [s.name for s in students],
            "Email": [s.email for s in students],
        }
    )
    df.to_csv(f"{BATCH}.csv")


async def add_to_db(students: list[Student]):
    pool = asyncpg.create_pool(
        dsn=os.getenv("PGDSN"), command_timeout=60, max_inactive_connection_lifetime=0
    )

    insert_str = "INSERT INTO student (roll_number, section, email, batch, hostel_id, name) VALUES "
    for student in students:
        if student.roll_number == "123102002":
            continue
        insert_str += f"('{student.roll_number}', '{student.section}', '{student.email}', {student.batch}, '{student.hostel_id}', '{student.name}'),\n"
    insert_str = insert_str[:-2] + ";"

    async with pool:
        await pool.execute(insert_str)


students = parse_roll()
# asyncio.run(add_to_db(students))
to_csv(students)
# for student in students:
#     print(student)
