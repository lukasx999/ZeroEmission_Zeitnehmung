#!/usr/bin/env python3

import sys
from pprint import pprint

from models     import teams, challenges, challenges_data, Session, Base, challenges_best_attempts
from sqlalchemy import create_engine, Select, Delete, func, insert, text



SERVER_IP   = "172.31.177.238"
DB_USER     = "mariadbclient"
DB_PASSWORD = "Kennwort1"
DB_PORT     = '3306'
DB_NAME     = 'Zeitmessung'


db_url     = f'mariadb+mariadbconnector://{DB_USER}:{DB_PASSWORD}@{SERVER_IP}:{DB_PORT}/{DB_NAME}'
engine_db  = create_engine(db_url)
Session_db = Session(bind=engine_db)

def setup_mariadb() -> tuple[list[str], list[str]]:
    try:
        Base.metadata.create_all(engine_db)

        teams_list:      list[str] = Session_db.scalars(Select(teams.name)).all()
        challenges_list: list[str] = Session_db.scalars(Select(challenges.name)).all()

        return (teams_list, challenges_list)
    except:
        print('Error',"Couldn't connect to server.", file=sys.stderr)
        sys.exit(1)




def calc_skidpad(t_min: float, t_team: float, n_tn: float, n_rt: float) -> float:
    a: float = 100 * (t_min / t_team)
    b: float = 1 + (n_tn / (100*n_rt))
    c: float = 1 + (n_tn / 100)

    return a * (b/c)

def calc_slalom(t_min: float, t_team: float, n_tn: float, n_rt: float) -> float:
    a: float = 100 * (t_min / t_team)
    b: float = 1 + (n_tn / (200*n_rt))
    c: float = 1 + (n_tn / 200)

    return a * (b/c)


# TODO: fix id auto increment
def populate_best_attempts() -> None:

    Session_db.query(challenges_best_attempts).delete()  # clear table
    team_count = len(Session_db.scalars(Select(teams.name)).all())

    # Get min time of team_id
    for i in range(1, team_count+1):
        entry: str = Session_db.scalar(Select(func.min(challenges_data.time)).where(challenges_data.tea_id == i))
        teamid: str = Session_db.scalar(Select(challenges_data.tea_id).where(challenges_data.tea_id == i))

        sql: str = insert(challenges_best_attempts).values(team_id=teamid, time=entry)
        Session_db.execute(sql)

    Session_db.commit()




def populate_leaderboard() -> None:
    # n_tn
    team_count = len(Session_db.scalars(Select(teams.name)).all())

    # t_team
    best_attempts = Session_db.scalar(Select(challenges_best_attempts.time))
    print(best_attempts)

    # n_rt: ranking (generated)





def main() -> int:
    teams_list, challenges_list = setup_mariadb()
    # print(teams_list)
    # print(challenges_list)

    # calc_skidpad(30, 3600, 3, 3600)

    populate_best_attempts()
    populate_leaderboard()
    return 0


if __name__ == "__main__":
    sys.exit(main())