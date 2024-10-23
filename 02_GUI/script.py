import sys
from pprint import pprint
from pathlib import Path

from models     import teams, challenges, challenges_data, Session, Base, challenges_best_attempts, leaderboard, teams
from sqlalchemy import create_engine, Select, Delete, func, insert, text, ScalarResult, asc as ascending, desc, alias, CursorResult
from fpdf import FPDF
import pandas as pd

CREATE_DOCS = False

SERVER_IP   = "192.168.13.180"
DB_USER     = "mariadbclient"
DB_PASSWORD = "Kennwort1"
DB_PORT     = '3306'
DB_NAME     = 'Zeitmessung'

FACTOR_POWER_WEIGHT = 1.0
FACTOR_ENERGY = 1.0
NUM_CATEGORIES = 3


db_url     = f'mariadb+mariadbconnector://{DB_USER}:{DB_PASSWORD}@{SERVER_IP}:{DB_PORT}/{DB_NAME}'
engine_db  = create_engine(db_url)
Session_db = Session(bind=engine_db)


def setup_mariadb() -> tuple[list[str], list[str]]:
    print("Connecting to server...")
    try:
        Base.metadata.create_all(engine_db)
        print("Connected to server.")

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
    if l_min is None or l_min == 0:
        l_min = l_team
    num: float = 1 + (n_tn / (200*n_rt))
    den: float = 1 + (n_tn / 200)
    result: float = 50 * (t_min / t_team) * (l_min / l_team) * (num / den)
        
    return result



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
        teams.category,
        (RANK() OVER (PARTITION BY challenges_data.tea_id, challenges_data.cmp_id ORDER BY challenges_data.time ASC)) AS rank_num
    FROM
        challenges_data
        JOIN teams on challenges_data.tea_id = teams.id
        JOIN challenges on challenges_data.cmp_id = challenges.id
        )

            SELECT Team, Challenge, time, power, energy, category
            FROM RankedTimes
            WHERE rank_num = 1 AND challenge = {challenge_id};
    """


def populate_best_attempts() -> None:

    challenge_count: int = len(Session_db.scalars(Select(challenges.name)).all())

    Session_db.query(challenges_best_attempts).delete()  # clear table

    for i in range(1, challenge_count+1):
        sql = get_best_attempts_sql(i)
        data: CursorResult = Session_db.execute(text(sql)).all()

        for column in data:
            team   = column[0]
            team_data = Session_db.scalar(Select(teams).where(teams.id == team))
            chal   = column[1]
            time   = column[2]
            power  = column[3]
            energy = column[4]
            category = column[5]
            power_weight_ratio = None
            if power is not None:
                power_weight_ratio = power / (team_data.vehicle_weight + team_data.driver_weight)
            
            Session_db.execute(insert(challenges_best_attempts).values(
                id=None, challenge_id=chal, team_id=team, time=time, power=power, energy=energy, category=category, power_weight_ratio=power_weight_ratio
            ))


    Session_db.commit()



def get_best_time_of_challenge(challenge_id: int, category_num: int) -> float:
    return Session_db.scalar(Select(challenges_best_attempts.time)
                             .where(challenges_best_attempts.challenge_id == challenge_id)
                             .where(challenges_best_attempts.category == category_num)
                             .order_by(ascending(challenges_best_attempts.time)))


#TODO: Fix this function same time values are not handled correctly
def get_rank(challenge_id: int, team: int, category_num: int) -> int:
    result: ScalarResult = Session_db.scalars(Select(challenges_best_attempts.team_id)
                             .where(challenges_best_attempts.challenge_id == challenge_id)
                             .where(challenges_best_attempts.category == category_num)
                             .order_by(ascending(challenges_best_attempts.time)))
    team_sequence: list[int] = result.fetchall()
    if team not in team_sequence:
        return -1
    return team_sequence.index(team) + 1
    

def get_energy(team_id: int, challenge_id: int, category_num: int) -> tuple[float]:

    energy_team: float = Session_db.scalar(Select(challenges_best_attempts.energy)
                                           .where(challenges_best_attempts.team_id      == team_id)
                                           .where(challenges_best_attempts.challenge_id == challenge_id)
                                           .where(challenges_best_attempts.category     == category_num))

    energy_min: float =  Session_db.scalar(Select(challenges_best_attempts.energy)
                                           .where(challenges_best_attempts.challenge_id == challenge_id)
                                           .where(challenges_best_attempts.category == category_num)
                                           .order_by(ascending(challenges_best_attempts.energy)))
    
    energy_max: float =  Session_db.scalar(Select(challenges_best_attempts.energy)
                                           .where(challenges_best_attempts.challenge_id == challenge_id)
                                           .where(challenges_best_attempts.category == category_num)
                                           .order_by(ascending(challenges_best_attempts.energy)))

    return (energy_team, energy_min, energy_max)


def get_power(team_id: int, challenge_id: int, category_num: int) -> tuple[float]:

    power_team: float = Session_db.scalar(Select(challenges_best_attempts.power)
                                           .where(challenges_best_attempts.team_id      == team_id)
                                           .where(challenges_best_attempts.challenge_id == challenge_id)
                                           .where(challenges_best_attempts.category     == category_num))

    
    power_max: float =  Session_db.scalar(Select(challenges_best_attempts.energy)
                                           .where(challenges_best_attempts.challenge_id == challenge_id)
                                           .where(challenges_best_attempts.category == category_num)
                                           .order_by(ascending(challenges_best_attempts.energy)))

    return (power_team, power_max)


def get_best_power_weight_ration(category_num: int) -> float:
    return Session_db.scalar(Select(challenges_best_attempts.power_weight_ratio)
                             .where(challenges_best_attempts.category == category_num)
                             .where(challenges_best_attempts.challenge_id == 3)
                             .order_by(ascending(challenges_best_attempts.power_weight_ratio)))

def get_weights(team) -> None:

    best_weight: float = Session_db.scalar(
        Select((teams.vehicle_weight + teams.driver_weight).label('weight'))
        .where(teams.category == team.category)
        .order_by(ascending('weight'))
    )


    return (team.driver_weight, team.vehicle_weight, best_weight)




def populate_leaderboard() -> None:
    # Sum up all points from all challenges and insert them into the `leaderboard` table

    Session_db.query(leaderboard).delete()  # clear table


    # -> n_tn
    for category_num in range(1, NUM_CATEGORIES+1):
        team_count:      int = len(Session_db.scalars(Select(teams.name)
                                                    .where(teams.category == category_num)).all())
        
        teamslist = Session_db.scalars(Select(teams).where(teams.category == category_num)).all()

        challenge_count: int = len(Session_db.scalars(Select(challenges.name)).all())

        # calculate the points for each challenge for each team
        for team in teamslist: # -> t_team
            points_sum: int = 0
            points_skidpad: int = 0
            points_slalom: int = 0
            points_acceleration: int = 0
            points_endurance: int = 0
            for challenge in range(1, challenge_count+1):

                # -> t_min: best time out of all teams
                best: float = get_best_time_of_challenge(challenge, category_num)

                # -> n_rt: ranking - based on time compared to other teams
                rank: int = get_rank(challenge, team.id, category_num)

                # -> t_team
                time: float|None = Session_db.scalar(Select(challenges_best_attempts.time)
                                                    .where(challenges_best_attempts.team_id == team.id)
                                                    .where(challenges_best_attempts.challenge_id == challenge)
                                                    .where(challenges_best_attempts.category == category_num))

                #assert time is not None  # Sanity check
                if time is None:
                    match challenge:  # Calculate points for current challenge
                        case 1:
                            points = 0
                            points_skidpad = points
                        case 2:
                            points = 0
                            points_slalom = points
                        case 3:
                            points = 0
                            points_acceleration = points
                        case 4:
                            points = 0
                            points_endurance = points

                    points_sum += points
                else:
                    match challenge:  # Calculate points for current challenge
                        case 1:
                            points = calc_skidpad(best, time, team_count, rank)
                            points_skidpad = points
                        case 2:
                            points = calc_slalom(best, time, team_count, rank)
                            points_slalom = points
                        case 3:
                            (power_team, power_max) = get_power(team.id, challenge, category_num)
                            if power_max is None:
                                power_max = 1000
                            if power_team is None:
                                power_team = power_max
                            best_ratio = get_best_power_weight_ration(category_num)
                            (weight_driver, weight_vehicle, best_weight) = get_weights(team)
                            points = calc_acceleration(best, time, team_count, rank, power_team, best_ratio, weight_vehicle, weight_driver)
                            points_acceleration = points
                        case 4:
                            (energy_team, energy_min, energy_max) = get_energy(team.id, challenge, category_num)
                            if energy_min is None:
                                energy_min = 1000
                            if energy_max is None:
                                energy_max = 1000
                            if energy_team is None:
                                energy_team = energy_max
                            points = calc_endurance(best, time, team_count, rank, energy_min, energy_team)
                            points_endurance = points

                    points_sum += points

            # Sum up all of the points and add them to the leaderboard table
            POINTS_DIGITS: int = 3
            Session_db.execute(insert(leaderboard).values(id=None, team_id=team.id, points=round(points_sum, POINTS_DIGITS), category=category_num, points_skidpad=round(points_skidpad, POINTS_DIGITS), points_slalom=round(points_slalom, POINTS_DIGITS), points_acceleration=round(points_acceleration, POINTS_DIGITS), points_endurance=round(points_endurance, POINTS_DIGITS)))

    Session_db.commit()

def category_name(category_num: int) -> str:
    if category_num == 1:
        return "FIA"
    elif category_num == 2:
        return "ZEC"
    else:
        return "Open"

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Leaderboard 2024', 0, 1, 'C')
        self.image("images_pdf\HTL-Weiz-Logo.png", 10, 8, 33)  # Adjust the path and size as needed
        self.image("images_pdf\ZEC-Logo.png", 167, 8, 33)  # Adjust the path and size as needed
        self.ln(20)  # Move to the next line after the images

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(10)

    def chapter_body(self, data):
        self.set_font('Arial', '', 12)
        col_widths = [20, 100, 30]
        for idx, row in enumerate(data, start=1):
            self.cell(col_widths[0], 10, f'{idx}', 1, 0, 'C')
            self.cell(col_widths[1], 10, f'{row[0]}', 1, 0, 'L')
            self.cell(col_widths[2], 10, f'{row[1]}', 1, 1, 'C')
        self.ln()

def export_leaderboard_to_pdf():
    pdf = PDF()
    pdf.add_page()

    for category_num in range(1, NUM_CATEGORIES+1):
        # Overall points
        pdf.chapter_title(f'Category {category_name(category_num)} - Overall Points')
        leaderboard_data = Session_db.execute(
            Select(teams.name, leaderboard.points)
            .join(teams, leaderboard.team_id == teams.id)
            .where(leaderboard.category == category_num)
            .order_by(desc(leaderboard.points))
        ).all()
        pdf.chapter_body(leaderboard_data)

    pdf.add_page()

    for category_num in range(1, NUM_CATEGORIES+1):
        # Skidpad points
        pdf.chapter_title(f'Category {category_name(category_num)} - Skidpad Points')
        skidpad_data = Session_db.execute(
            Select(teams.name, leaderboard.points_skidpad)
            .join(teams, leaderboard.team_id == teams.id)
            .where(leaderboard.category == category_num)
            .order_by(desc(leaderboard.points_skidpad))
        ).all()
        pdf.chapter_body(skidpad_data)

        # Slalom points
        pdf.chapter_title(f'Category {category_name(category_num)} - Slalom Points')
        slalom_data = Session_db.execute(
            Select(teams.name, leaderboard.points_slalom)
            .join(teams, leaderboard.team_id == teams.id)
            .where(leaderboard.category == category_num)
            .order_by(desc(leaderboard.points_slalom))
        ).all()
        pdf.chapter_body(slalom_data)

        # Acceleration points
        pdf.chapter_title(f'Category {category_name(category_num)} - Acceleration Points')
        acceleration_data = Session_db.execute(
            Select(teams.name, leaderboard.points_acceleration)
            .join(teams, leaderboard.team_id == teams.id)
            .where(leaderboard.category == category_num)
            .order_by(desc(leaderboard.points_acceleration))
        ).all()
        pdf.chapter_body(acceleration_data)

        # Endurance points
        pdf.chapter_title(f'Category {category_name(category_num)} - Endurance Points')
        endurance_data = Session_db.execute(
            Select(teams.name, leaderboard.points_endurance)
            .join(teams, leaderboard.team_id == teams.id)
            .where(leaderboard.category == category_num)
            .order_by(desc(leaderboard.points_endurance))
        ).all()
        pdf.chapter_body(endurance_data)

    pdf.output('leaderboard.pdf')

def export_leaderboard_to_excel():
    writer = pd.ExcelWriter('leaderboard.xlsx', engine='xlsxwriter')

    for category_num in range(1, NUM_CATEGORIES+1):
        # Overall points
        leaderboard_data = Session_db.execute(
            Select(teams.name, leaderboard.points, leaderboard.points_skidpad, leaderboard.points_slalom, leaderboard.points_acceleration, leaderboard.points_endurance)
            .join(teams, leaderboard.team_id == teams.id)
            .where(leaderboard.category == category_num)
            .order_by(desc(leaderboard.points))
        ).all()
        df = pd.DataFrame(leaderboard_data, columns=['Team', 'Points', 'Skidpad Points', 'Slalom Points', 'Acceleration Points', 'Endurance Points'])
        df.to_excel(writer, sheet_name=f'Category {category_name(category_num)} - Overall', index=False)

        # Skidpad points
        skidpad_data = Session_db.execute(
            Select(teams.name, leaderboard.points_skidpad)
            .join(teams, leaderboard.team_id == teams.id)
            .where(leaderboard.category == category_num)
            .order_by(desc(leaderboard.points_skidpad))
        ).all()
        df = pd.DataFrame(skidpad_data, columns=['Team', 'Skidpad Points'])
        df.to_excel(writer, sheet_name=f'Category {category_name(category_num)} - Skidpad', index=False)

        # Slalom points
        slalom_data = Session_db.execute(
            Select(teams.name, leaderboard.points_slalom)
            .join(teams, leaderboard.team_id == teams.id)
            .where(leaderboard.category == category_num)
            .order_by(desc(leaderboard.points_slalom))
        ).all()
        df = pd.DataFrame(slalom_data, columns=['Team', 'Slalom Points'])
        df.to_excel(writer, sheet_name=f'Category {category_name(category_num)} - Slalom', index=False)

        # Acceleration points
        acceleration_data = Session_db.execute(
            Select(teams.name, leaderboard.points_acceleration)
            .join(teams, leaderboard.team_id == teams.id)
            .where(leaderboard.category == category_num)
            .order_by(desc(leaderboard.points_acceleration))
        ).all()
        df = pd.DataFrame(acceleration_data, columns=['Team', 'Acceleration Points'])
        df.to_excel(writer, sheet_name=f'Category {category_name(category_num)} - Acceleration', index=False)

        # Endurance points
        endurance_data = Session_db.execute(
            Select(teams.name, leaderboard.points_endurance)
            .join(teams, leaderboard.team_id == teams.id)
            .where(leaderboard.category == category_num)
            .order_by(desc(leaderboard.points_endurance))
        ).all()
        df = pd.DataFrame(endurance_data, columns=['Team', 'Endurance Points'])
        df.to_excel(writer, sheet_name=f'Category {category_name(category_num)} - Endurance', index=False)

    writer.close()



def main() -> int:
    teams_list, challenges_list = setup_mariadb()

    populate_best_attempts()
    populate_leaderboard()
    if CREATE_DOCS:
        export_leaderboard_to_pdf()
        export_leaderboard_to_excel()

    return 0



if __name__ == "__main__":
    sys.exit(main())
