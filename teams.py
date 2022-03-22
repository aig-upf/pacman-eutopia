import json


def get_team_name(team) -> str:
    return team["name"]


def get_team_id(team) -> int:
    return team["id"]


def get_team_repository(team) -> str:
    return team["repository"]


def get_team_last_commit(team) -> str:
    return team["last_commit"]


def get_list_members(team) -> list:
    return team["members"]


def get_member_name(member) -> str:
    return member["name"]


def get_member_id(member) -> str:
    return member["id"]


def main():
    with open("teams_upf-ai22.json", "r") as f:
        team_data = json.load(f)
        for team in team_data["teams"]:
            print(f"Team {get_team_name(team)} (#{get_team_id(team)}):\n"
                  f"\t- repository: {get_team_repository(team)} (commit: {get_team_last_commit(team)})\n"
                  f"\t- members:\n" +
                  '\n'.join(f"\t\t- {get_member_name(m)} (#{get_member_id(m)})" for m in get_list_members(team)) + "\n")


if __name__ == "__main__":
    main()
