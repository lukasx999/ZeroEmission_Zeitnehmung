#!/usr/bin/env python3

import sys
from pprint import pprint

from models     import teams, challenges, challenges_data, Session, Base, challenges_best_attempts, leaderboard
from sqlalchemy import create_engine, Select, Delete, func, insert, text, ScalarResult, asc as ascending, alias, CursorResult

SERVER_IP   = "10.0.0.242"
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




def calc_skidpad(t_min: float, t_team: float,
                 n_tn:  float, n_rt:   float) -> float:

    num: float = 1 + (n_tn / (100*n_rt))
    den: float = 1 + (n_tn / 100)
    return 100 * (t_min / t_team) * (num/den)



def calc_slalom(t_min: float, t_team: float,
                n_tn:  float, n_rt:   float) -> float:

    num: float = 1 + (n_tn / (200*n_rt))
    den: float = 1 + (n_tn / 200)
    return 100 * (t_min / t_team) * (num/den)



def calc_acceleration(t_min: float, t_team: float,
                      n_tn:  float, n_rt:   float,
                      mean_power: float, l_min: float,
                      vehicle_weight: float, driver_weight: float) -> float:

    l_team: float = mean_power / (vehicle_weight + driver_weight)

    num: float = 1 + (n_tn / (200*n_rt))
    den: float = 1 + (n_tn/200)
    return 50 * (t_min/t_team) * (l_min/l_team) * (num/den)



def calc_endurance(t_min: float, t_team: float,
                   n_tn:  float, n_rt:   float,
                   w_min:  float, w_team:   float) -> float:

    points_endtime:   float =  100 * (t_min/t_team)  # End Time
    points_endenergy: float =  150 * (w_min/w_team) # End energy
    return points_endtime + points_endenergy




def get_best_attempts_sql(challenge_id: int) -> str:
    return f"""
    WITH RankedTimes AS (
    SELECT
        teams.id AS team,
        challenges.id AS challenge,
        challenges_data.cmp_id,
        challenges_data.attempt_nr,
        challenges_data.timepenalty,
        challenges_data.time,
        challenges_data.power,
        challenges_data.energy,
        (RANK() OVER (PARTITION BY challenges_data.tea_id, challenges_data.cmp_id ORDER BY challenges_data.time ASC)) AS rank_num
    FROM
        challenges_data
        JOIN teams on challenges_data.tea_id = teams.id
        JOIN challenges on challenges_data.cmp_id = challenges.id
        )

            SELECT Team, Challenge, time, power, energy
            FROM RankedTimes
            WHERE rank_num = 1 AND challenge = {challenge_id};
    """




def populate_best_attempts() -> None:

    challenge_count: int = len(Session_db.scalars(Select(challenges.name)).all())

    Session_db.query(challenges_best_attempts).delete()  # clear table


    # best: list[tuple[str]] = Session_db.execute(text(sql)).all()
    # pprint(best)

    for i in range(1, challenge_count+1):
        sql = get_best_attempts_sql(i)
        data: CursorResult = Session_db.execute(text(sql)).all()
        # pprint(data)

        for column in data:
            team   = column[0]
            chal   = column[1]
            time   = column[2]
            power  = column[3]
            energy = column[4]
            Session_db.execute(insert(challenges_best_attempts).values(
                id=None, challenge_id=chal, team_id=team, time=time, power=power, energy=energy
            ))


    Session_db.commit()



def get_best_time_of_challenge(challenge_id: int) -> float:
    return Session_db.scalar(Select(challenges_best_attempts.time)
                             .where(challenges_best_attempts.challenge_id == challenge_id)
                             .order_by(ascending(challenges_best_attempts.time)))


def get_rank(challenge_id: int, team: int) -> int:
    result: ScalarResult = Session_db.scalars(Select(challenges_best_attempts.team_id)
                             .where(challenges_best_attempts.challenge_id == challenge_id)
                             .order_by(ascending(challenges_best_attempts.time)))

    team_sequence: list[int] = result.fetchall()
    return team_sequence.index(team)+1




def get_energy(team_id: int, challenge_id: int) -> tuple[float]:

    energy_team: float = Session_db.scalar(Select(challenges_best_attempts.energy)
                                           .where(challenges_best_attempts.team_id      == team_id)
                                           .where(challenges_best_attempts.challenge_id == challenge_id))

    energy_min: float =  Session_db.scalar(Select(challenges_best_attempts.energy)
                                           .where(challenges_best_attempts.challenge_id == challenge_id)
                                           .order_by(ascending(challenges_best_attempts.energy)))

    return (energy_team, energy_min)



def get_weights(team_id: int) -> None:

    sql: str = """SELECT (vehicle_weight + driver_weight) AS weight FROM teams ORDER BY weight ASC; """
    best_weight: CursorResult = Session_db.execute(text(sql)).fetchone()

    weight_driver:  float = Session_db.scalar(Select(teams.driver_weight) .where(teams.id == team_id))
    weight_vehicle: float = Session_db.scalar(Select(teams.vehicle_weight).where(teams.id == team_id))

    return (weight_driver, weight_vehicle, best_weight[0])




def populate_leaderboard() -> None:
    # Sum up all points from all challenges and insert them into the `leaderboard` table

    Session_db.query(leaderboard).delete()  # clear table

    # -> n_tn
    team_count:      int = len(Session_db.scalars(Select(teams.name)).all())

    challenge_count: int = len(Session_db.scalars(Select(challenges.name)).all())

    # calculate the points for each challenge for each team

    for team in range(1, team_count+1): # -> t_team

        points_sum: int = 0
        for challenge in range(1, challenge_count+1):

            # -> t_min: best time out of all teams
            best: float = get_best_time_of_challenge(challenge)

            # -> n_rt: ranking - based on time compared to other teams
            rank: int = get_rank(challenge, team)

            # -> t_team
            time: float|None = Session_db.scalar(Select(challenges_best_attempts.time)
                                                 .where(challenges_best_attempts.team_id      == team)
                                                 .where(challenges_best_attempts.challenge_id == challenge))

            assert time is not None  # Sanity check


            mean_power: float = Session_db.scalar(Select(challenges_best_attempts.power)
                                             .where(challenges_best_attempts.team_id      == team)
                                             .where(challenges_best_attempts.challenge_id == challenge))


            match challenge:  # Calculate points for current challenge
                case 1:
                    points = calc_skidpad(best, time, team_count, rank)
                case 2:
                    points = calc_slalom(best, time, team_count, rank)
                case 3:
                    assert mean_power is not None
                    (weight_driver, weight_vehicle, best_weight) = get_weights(team)
                    points = calc_acceleration(best, time, team_count, rank, mean_power, best_weight, weight_vehicle, weight_driver)
                case 4:
                    (energy_team, energy_min) = get_energy(team, challenge)
                    points = calc_endurance(best, time, team_count, rank, energy_min, energy_team)

            points_sum += points

        # Sum up all of the points and add them to the leaderboard table
        POINTS_DIGITS: int = 3
        Session_db.execute(insert(leaderboard).values(id=None, team_id=team, points=round(points_sum, POINTS_DIGITS)))

    Session_db.commit()






def main() -> int:
    teams_list, challenges_list = setup_mariadb()

    populate_best_attempts()
    populate_leaderboard()

    return 0



if __name__ == "__main__":
    sys.exit(main())
