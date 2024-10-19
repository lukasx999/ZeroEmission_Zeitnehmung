from flask import Flask, render_template, jsonify, url_for, request
from sqlalchemy import create_engine, Select, asc, desc, Table, MetaData, text
from models import teams,challenges,challenges_data,Session,Base,raw_data,leaderboard
import paho.mqtt.client as mqtt
import json
from dateutil import parser
import threading

# Database configuration
DB_USER     = "mariadbclient"   # Replace "mariadbclient" with the actual database user
DB_PASSWORD = "Kennwort1"       # Replace "Kennwort1" with the actual database password

# MQTT configuration
MQTT_USER     = "mqttclient"    # Replace "mqttclient" with the actual MQTT username
MQTT_PASSWORD = "Kennwort1"     # Replace "Kennwort1" with the actual MQTT password


# constants for Database configurations
SERVER_IPADRESS = "127.0.0.1"
MQTT_PORT       = 1883
DB_PORT         = '3306'
DB_NAME         = 'Zeitmessung'

db_url = f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{SERVER_IPADRESS}:{DB_PORT}/{DB_NAME}'
engine_db = create_engine(db_url)
Session_db = Session(bind = engine_db)

Base.metadata.create_all(bind=engine_db)


def on_connect(client, userdata, flags, rc):
    print("connected!")
    client.subscribe("esp32/timestamp",qos=2)


def on_message(client, userdata, message):
    print("message!")
    payload = message.payload.decode("utf-8")

    if message.topic == "esp32/timestamp" :
        data_json = json.loads(payload)
        data = raw_data()

        if 'esp_id' in data_json:
            data.esp_id = data_json['esp_id']

        if 'timestamp' in data_json:
            data.timestamp = parser.isoparse(data_json['timestamp'])

        Session_db.add(data)
        Session_db.commit()

# def start_mqtt_client():
#     client = mqtt.Client()
#     client.on_connect = on_connect
#     client.on_message = on_message
#     client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
#     client.connect(SERVER_IPADRESS, MQTT_PORT, 60)
#     client.loop_start()

# def start_mqtt_thread():
#     mqtt_thread = threading.Thread(target=start_mqtt_client)
#     mqtt_thread.daemon = True
#     mqtt_thread.start()

# start_mqtt_thread()



app = Flask(__name__)



def clean_dict(dictionary):
    return {key: value for key, value in dictionary.items() if key[0] != '_'}


@app.route('/')
def Zeitmessung():
    return render_template('01_Home/home.html')

@app.route('/Bestenliste')
def Bestenliste():
    Session_db.commit()

    # query = """\
    #     SELECT teams.name as Team, points as TotalPoints FROM `leaderboard`
    #     JOIN teams on team_id = teams.id;
    #     """
    #
    # raw_data = Session_db.execute(text(query)).fetchall()
    # return render_template('02_Bestenliste/best.html', leaderboard_data=raw_data)

    return render_template('02_Bestenliste/leaderboards.html')

@app.route('/Bestenliste/<selected_category>')
def leaderboard_page(selected_category):
    # shows the best time of each team for every challenge
    Session_db.commit()

    return render_template('02_Bestenliste/leaderboard_page.html', category=selected_category)



@app.route('/Teamuebersicht')
def Teamuebersicht():
    Session_db.commit()
    team = Session_db.scalars(Select(teams)).all()

    return render_template('03_Teamuebersicht/teams.html',teams=team)

@app.route('/Teamuebersicht/<selected_team_name>')
def team_page(selected_team_name):
    Session_db.commit()
    selected_team = Session_db.scalar(Select(teams).where(teams.name==selected_team_name))
    
    challenges_all = Session_db.scalars(Select(challenges)).all()
    team_data = []

    for challenge in challenges_all:
        data = Session_db.scalars(Select(challenges_data).where(challenges_data.tea_id==selected_team.id,challenges_data.cmp_id==challenge.id).order_by(asc(challenges_data.attempt_nr))).all()
        data_best = Session_db.scalars(Select(challenges_data).where(challenges_data.tea_id==selected_team.id,challenges_data.cmp_id==challenge.id).order_by(asc(challenges_data.time))).first()
        team_data.append((challenge,data,data_best)) 

    return render_template('03_Teamuebersicht/team_page.html',team_name=selected_team_name,data=team_data)



@app.route('/Einzelauswertung')
def Einzelauswertung():
    Session_db.commit()
    cmp = Session_db.scalars(Select(challenges)).all()

    return render_template('04_Einzelauswertung/competitions.html',competitions=cmp)

@app.route('/Einzelauswertung/<selected_cmp_name>')
def comp_page(selected_cmp_name):
    selected_categorie = request.args.get('selected_category')
    # shows the best time of each team for every challenge
    Session_db.commit()

    return render_template('04_Einzelauswertung/competition_page.html', cmp_name=selected_cmp_name, category=selected_categorie)




# @app.route('/update_leaderboard', methods=['GET'])
# def update_leaderboard():
#     Session_db.commit()

#     query = """\
#         SELECT teams.name as Team, points as TotalPoints FROM `leaderboard`
#         JOIN teams on team_id = teams.id;
#         """

#     raw_data = Session_db.execute(text(query)).fetchall()
#     data: list[dict[str: str]] = [dict(row._asdict()) for row in raw_data]
#     return jsonify(data)


@app.route('/update_leaderboard/<selected_category>', methods=['GET'])
def update_leaderboard(selected_category):
    Session_db.commit()

    query = """\
        SELECT teams.name as Team, points as TotalPoints FROM `leaderboard`
        JOIN teams on team_id = teams.id
        WHERE leaderboard.category = :selected_category
        ORDER BY TotalPoints DESC;
        """

    raw_data = Session_db.execute(text(query), {'selected_category': selected_category}).fetchall()
    data: list[dict[str: str]] = [dict(row._asdict()) for row in raw_data]
    return jsonify(data)
    # Session_db.commit()

    # raw_data = Session_db.scalars(Select(teams.name, leaderboard.points)
    #                               .join(teams, leaderboard.team_id == teams.id)
    #                               .where(leaderboard.category == selected_category)
    #                               .order_by(desc(leaderboard.points))).all()
    
    # print("raw_data",raw_data)

    # data: list[dict[str: str]] = [dict(row._asdict()) for row in raw_data]
    # return jsonify(data)


@app.route('/update_team_board/<selected_team_name>', methods=['GET'])
def update_team_board(selected_team_name):
    Session_db.commit()

    selected_team = Session_db.scalar(Select(teams).where(teams.name==selected_team_name))
    challenges_all = Session_db.scalars(Select(challenges)).all()

    team_data = []
    for challenge in challenges_all:
        raw_data = Session_db.scalars(Select(challenges_data).where(challenges_data.tea_id==selected_team.id,challenges_data.cmp_id==challenge.id).order_by(asc(challenges_data.attempt_nr))).all()


        data_best = Session_db.scalars(Select(challenges_data).where(challenges_data.tea_id==selected_team.id,challenges_data.cmp_id==challenge.id).order_by(asc(challenges_data.time))).first()

        challenge_dict = clean_dict(challenge.__dict__) 
        data_best_dict = clean_dict(data_best.__dict__) if data_best is not None else {'time':'/'}
        data_dict = [clean_dict(row.__dict__) for row in raw_data] if raw_data is not None else {}

        for row in data_dict:
            row['starttime'] = row['starttime'].strftime('%d.%m.%Y, %H:%M:%S.%f')[:-3] if row['starttime'] else '/'
            row['stoptime'] = row['stoptime'].strftime('%d.%m.%Y, %H:%M:%S.%f')[:-3] if row['stoptime'] else '/'
            row['timepenalty'] = row['timepenalty'] if row['timepenalty'] else '/'

        team_data.append((challenge_dict,data_dict,data_best_dict))
            
    return jsonify(team_data)

@app.route('/update_challenge/<selected_cmp_name>/<selected_category>', methods=['GET'])
def update_challenge(selected_cmp_name,selected_category):
    Session_db.commit()

    
    # query: str = f"""\
    #                 FROM `challenges_best_attempts`
    #               JOIN teams ON team_id = teams.id
    #                JOIN challenges ON challenge_id = challenges.id
    #                 WHERE challenges.name = :selected_cmp_name" AND challenges.category = :selected_category"
    #                  ORDER BY time ASC;

    # 
    # 
    #                  """

    selected_cmp_id = 1 if selected_cmp_name == "Skidpad" else 2 if selected_cmp_name == "Slalom" else 3 if selected_cmp_name == "Acceleration" else "Endurance"

    pstr = "points_skidpad" if selected_cmp_id == 1 else "points_slalom" if selected_cmp_id == 2 else "points_acceleration" if selected_cmp_id == 3 else "points_endurance"

    print("selected_cmp_name",selected_cmp_name)
    print("selected_cmp_id",selected_cmp_id)
    print("pstr",pstr)
    query = """\
        SELECT teams.name as Team, """+ pstr+ """ as TotalPoints FROM `leaderboard`
        JOIN teams on team_id = teams.id
        WHERE leaderboard.category = :selected_category
        ORDER BY TotalPoints DESC;
        """

    print("query",query)
    print("selected_category",selected_category)
    raw_data = Session_db.execute(text(query), {'selected_category': selected_category}).fetchall()
    print("raw_data",raw_data)

    data: list[dict[str: str]] = [dict(row._asdict()) for row in raw_data]

    return jsonify(data)


if __name__ == '__main__':
    app.run()






