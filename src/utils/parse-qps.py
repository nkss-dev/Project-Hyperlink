import json

import config
from apiclient import errors
from apiclient.discovery import build
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


class GoogleDrive:
    def __init__(self):
        SCOPES = ("https://www.googleapis.com/auth/drive",)

        if not config.GOOGLE_REFRESH_TOKEN:
            flow = InstalledAppFlow.from_client_config(
                config.google_client_config, SCOPES
            )
            creds = flow.run_local_server(port=0)
            print(
                "Set the environment variable GOOGLE_REFRESH_TOKEN to",
                json.loads(creds.to_json())["refresh_token"],
                "and run this program again.",
            )
            exit(1)

        creds = Credentials.from_authorized_user_info(
            {
                "client_id": config.GOOGLE_CLIENT_ID,
                "client_secret": config.GOOGLE_CLIENT_SECRET,
                "refresh_token": config.GOOGLE_REFRESH_TOKEN,
            },
            SCOPES,
        )
        creds.refresh(Request())

        self.service = build("drive", "v3", credentials=creds)

    def listItems(self, query: str) -> list[dict[str, str]]:
        """Return all items matching the given query"""
        try:
            response = (
                self.service.files()
                .list(
                    q=query,
                    fields="nextPageToken, files(id, name)",
                )
                .execute()
            )
        except errors.HttpError:
            return []
        files = response.get("files", [])
        nextPageToken = response.get("nextPageToken")

        while nextPageToken:
            try:
                response = (
                    self.service.files()
                    .list(
                        q=query,
                        fields="nextPageToken, files(id, name)",
                        pageToken=nextPageToken,
                    )
                    .execute()
                )
            except errors.HttpError:
                return []
            files.extend(response.get("files", []))
            nextPageToken = response.get("nextPageToken")

        return files


drive = GoogleDrive()
question_papers_folder_id = "12pGDoyfxrBXkv7kPoPIoXuU2ec2cEL0z"
question_papers = drive.listItems(f"'{question_papers_folder_id}' in parents")
for paper in question_papers:
    print(paper["name"])
exit(1)

months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def getDups(papers):
    from collections import Counter

    return [k for k, v in Counter(papers).items() if v > 1]


def getName(old_name):
    name, ext = old_name.split(".")

    for month in months:
        if month in name:
            name = " ".join([substr.strip() for substr in name.split(month)])

    return f"{name.strip()}.{ext}"


papers = [getName(paper["name"]) for paper in question_papers]
duplicates = getDups(papers)

for paper in question_papers:
    new_name = getName(paper["name"])

    if new_name in duplicates:
        continue

    if new_name == paper["name"]:
        continue

    print(paper["name"], "->", new_name)
    drive.service.files().update(
        fileId=paper["id"],
        body={"name": new_name},
    ).execute()
