from dataclasses import dataclass


@dataclass
class ClubDiscord:
    club_name: str
    guild_id: int
    guest_role: int | None
    member_role: int | None


def parse_club_discord(club_discord_dict) -> ClubDiscord:
    # Uncomment when fetching is done from breadboard

    # def is_valid(field: str, kind: str = "String"):
    #     if club_discord_dict[field]["Valid"]:
    #         return club_discord_dict.pop(field)[kind]
    #     return None

    # club_discord_dict["guest_role"] = is_valid("guest_role")
    # club_discord_dict["memebr_role"] = is_valid("memebr_role")

    return ClubDiscord(**club_discord_dict)
