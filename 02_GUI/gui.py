from pathlib import Path
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime, timedelta
from models import teams,challenges,challenges_data,Session,Base
from sqlalchemy import create_engine, Select,Delete
from dateutil.parser import parse
from functools import partial
import paho.mqtt.client as mqtt
import json
from dateutil import parser
import sys
import platform
from sqlalchemy.dialects.mysql.mariadb import *
from mariadb import *


# Server configuration
SERVER_IP   = "192.168.0.211" # Replace "IP-Address" with the actual IP address of the RasPi

# MQTT configuration
MQTT_USER = "mqttclient"        # Replace "mqttclient" with the actual MQTT username 
MQTT_PASSWORD = "Kennwort1"     # Replace "Kennwort1" with the actual MQTT password 

# Database configuration
DB_USER = "mariadbclient"       # Replace "mariadbclient" with the actual database user 
DB_PASSWORD = "Kennwort1"       # Replace "Kennwort1" with the actual database password 



# constants for MQTT and Database configurations
MQTT_PORT = 1883  
DB_PORT = '3306'
DB_NAME = 'Zeitmessung'


db_url = f'mariadb+mariadbconnector://{DB_USER}:{DB_PASSWORD}@{SERVER_IP}:{DB_PORT}/{DB_NAME}'
engine_db = create_engine(db_url)
Session_db = Session(bind = engine_db)

OUTPUT_PATH = Path(__file__).parent

if platform.system() == "Linux":
    ASSETS_PATH = OUTPUT_PATH / Path(r"assets/frame0")
else:
    ASSETS_PATH = OUTPUT_PATH / Path(r"assets\frame0")

TIME_FORMAT = "%H:%M:%S.%f"

def relative_to_assets(path: str) -> Path:
    return  Path(r"assets\frame0") / Path(path)

window = Tk()
window.geometry("1440x900")
window.configure(bg = "#FFFFFF")
window.title("Zero Emission Challenge Timing")



canvas = Canvas(
        window,
        bg = "#FFFFFF",
        height = 900,
        width = 1440,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge"
)
canvas.place(x = 0, y = 0)

# Variables for timing management system
# Challenge and team selection 
selected_challenge = StringVar()
selected_team = StringVar()

# Lists to store information about teams and challenges
teams_list = []
challenges_list = []

# List of ESP32 devices
devices = [""]

# Selected ESP32 devices 
start1_selected = StringVar()
start2_selected = StringVar()
finish1_selected = StringVar()
finish2_selected = StringVar()

# Lists to store the last four timestamps for each selected ESP32 device
start1_timestamps = []
start2_timestamps = []
finish1_timestamps = []
finish2_timestamps = []

# Variables for the selected timestamp 
selected_timestamp_start1 = StringVar()
selected_timestamp_start2 = StringVar()
selected_timestamp_finish1 = StringVar()
selected_timestamp_finish2 = StringVar()

# Database-related variables
challenge_db = None
start_timestamp = None
finish_timestamp = None
laptime = None
timepenalty = None
totaltime = None
attemptnr = None

# Variable indicating the status of the GUI (True if active, False if not)
status = True


def loadConfig():
    config_path = Path(r"config\config.json")
    if config_path.exists():
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
            devices.append(config.get("start1", ""))
            selected_challenge.set(config.get("challenge", ""))
            combo_challenge.set(config.get("challenge", ""))
            update_challenge(None)
            start1_selected.set(config.get("start1", ""))
            start2_selected.set(config.get("start2", ""))
            finish1_selected.set(config.get("finish1", ""))
            finish2_selected.set(config.get("finish2", ""))
    else:
        messagebox.showerror('Error', "Config file not found.")

def setup_mariadb():
    try:
        Base.metadata.create_all(engine_db)
        global teams_list
        global challenges_list

        teams_list = Session_db.scalars(Select(teams.name)).all()
        challenges_list = Session_db.scalars(Select(challenges.name)).all()
    except:
        messagebox.showerror('Error',"Couldn't connect to server.")
        sys.exit()

def update_challenge(event):
    selected_challenge_name = selected_challenge.get()

    global challenge_db
    challenge_db = Session_db.scalar(Select(challenges).where(challenges.name == selected_challenge_name))

    canvas.itemconfig(penalty_id,text=str(challenge_db.penalty))
    update_timepenalty()

def update_team(event):
    team_db = Session_db.scalar(Select(teams).where(teams.name == selected_team.get()))
    if team_db and challenge_db:
        next_attempt = Session_db.scalar(
            Select(challenges_data.attempt_nr)
            .where(challenges_data.tea_id == team_db.id, challenges_data.cmp_id == challenge_db.id)
            .order_by(challenges_data.attempt_nr.desc())
        )
        next_attempt = next_attempt + 1 if next_attempt is not None else 1
        print(next_attempt)
        entry_attempt.delete(0, 'end')
        entry_attempt.insert(0, next_attempt if next_attempt else 1)
        update_attemptnr()
    else:
        messagebox.showerror('Error','Please input team.')

def update_start_timestamp(man_timestamp):
    global start_timestamp
    
    if man_timestamp == None:
        start1 = datetime.fromisoformat(selected_timestamp_start1.get()) if selected_timestamp_start1.get() not in ['','None'] else None
        start2 = datetime.fromisoformat(selected_timestamp_start2.get()) if selected_timestamp_start2.get() not in ['','None'] else None

        if start1 and start2:
            timedifferenz = start1 - start2
            start_timestamp = start1 - timedifferenz/2
        elif start1 != None:
            start_timestamp = start1
        elif start2 != None:
            start_timestamp = start2
    else:
        try:
            start_timestamp = parse(man_timestamp,fuzzy=True,dayfirst=True)
            entry_start.delete(0,'end')
            selected_timestamp_start1.set(None)
            selected_timestamp_start2.set(None)
        except:
            messagebox.showerror("Error","Couldn't convert manual Input: Inputformat: hh:mm:ss.ssssss")
            return
                                    

    canvas.itemconfig(start_timestamp_id,text=start_timestamp.time()) if start_timestamp != None else None
    update_laptime(None)
    
def update_finish_timestamp(man_timestamp):
    global finish_timestamp

    if man_timestamp == None:
        finish1 = datetime.fromisoformat(selected_timestamp_finish1.get()) if selected_timestamp_finish1.get() not in ['','None'] else None
        finish2 = datetime.fromisoformat(selected_timestamp_finish2.get()) if selected_timestamp_finish2.get() not in ['','None'] else None

        if finish1 and finish2:
            timedifferenz = finish1 - finish2
            finish_timestamp = finish1 - timedifferenz/2
        elif finish1 != None:
            finish_timestamp = finish1
        elif finish2 != None:
            finish_timestamp = finish2
    else:
        try:
            finish_timestamp = parse(man_timestamp,fuzzy=True,dayfirst=True)
            entry_finish.delete(0,'end')
            selected_timestamp_finish1.set(None)
            selected_timestamp_finish2.set(None)
        except:
            messagebox.showerror("Error","Couldn't convert manual Input: Inputformat: hh:mm:ss.ssssss")
            return

    canvas.itemconfig(finish_timestamp_id,text=finish_timestamp.time()) if finish_timestamp != None else None
    update_laptime(None)

def update_laptime(man_laptime):
    global laptime
    global start_timestamp
    global finish_timestamp

    if man_laptime == None:
        if start_timestamp and finish_timestamp:
            laptime = (finish_timestamp - start_timestamp).total_seconds()
    else:
        try:
            laptime = float(man_laptime.replace(',','.'))
            entry_laptime.delete(0,'end')

            start_timestamp = None
            finish_timestamp = None
            selected_timestamp_start1.set(None)
            selected_timestamp_start2.set(None)
            canvas.itemconfig(start_timestamp_id,text="")

            selected_timestamp_finish1.set(None)
            selected_timestamp_finish2.set(None)
            canvas.itemconfig(finish_timestamp_id,text="")
        except:
            messagebox.showerror("Error","Couldn't convert manual Input. Please input as floating-point number.")
            return
    
    canvas.itemconfig(laptime_id, text=str(round(laptime,3))) if laptime != None else None
    update_totaltime()

def update_timepenalty():
    global timepenalty

    try:
        hatsdown = int(entry_timepenalty.get()) if entry_timepenalty.get() != '' else 0
    except:
        messagebox.showerror("Warning","Couldn't convert number. Please input as integer number.")
        return

    timepenalty = float(challenge_db.penalty * hatsdown ) if challenge_db != None else None
    canvas.itemconfig(timepenalty_id,text=str(timepenalty)) if timepenalty != None else None
    update_totaltime()

def update_energy():
    global energy

    try:
        energy = int(entry_energy.get()) if entry_energy.get() != '' else 0
    except:
        messagebox.showerror("Warning","Couldn't convert number. Please input as integer number.")
        return

    #timepenalty = float(challenge_db.penalty * hatsdown ) if challenge_db != None else None
    #canvas.itemconfig(timepenalty_id,text=str(timepenalty)) if timepenalty != None else None
    #update_totaltime()
    
def update_totaltime():
    global totaltime

    totaltime = laptime + timepenalty if laptime is not None and timepenalty is not None else laptime or timepenalty
    canvas.itemconfig(totaltime_id,text=str(round(totaltime,3))) if totaltime != None else None

def update_attemptnr():
    global attemptnr

    attemptnr = int(entry_attempt.get()) if entry_attempt.get() != '' else None

def confirm():
    team_db = Session_db.scalar(Select(teams).where(teams.name == selected_team.get()))

    
    data = challenges_data()
    if team_db:
        data.tea_id = team_db.id
    else:
        messagebox.showerror('Error','Please input team.')
        return
    
    if challenge_db:
        data.cmp_id = challenge_db.id 
    else:
        messagebox.showerror('Error','Please input challenge.')
        return
    
    attempt_exists = Session_db.execute(Select(challenges_data).where(challenges_data.tea_id==team_db.id,challenges_data.cmp_id==challenge_db.id,challenges_data.attempt_nr==attemptnr)).first()
    if attempt_exists:
            answer = messagebox.askquestion('Error','Attempt for this team and challenge already exists. Replace?')
            if answer == 'yes':
                Session_db.execute(Delete(challenges_data).where(challenges_data.tea_id==team_db.id,challenges_data.cmp_id==challenge_db.id,challenges_data.attempt_nr==attemptnr))
                Session_db.commit()
                data.attempt_nr = attemptnr 
            else:
                return
    else:
        if attemptnr:
            data.attempt_nr = attemptnr 
        else:
            messagebox.showerror('Error','Please input attempt number.')
            return
    
    data.starttime = start_timestamp 
    data.stoptime = finish_timestamp
    data.timepenalty = timepenalty
    

    if laptime:
        data.time = totaltime 
    else:
        messagebox.showerror('Error','Please select lap time.')
        return

    


    Session_db.add(data)
    Session_db.commit()

    decline()

def decline():
    global start_timestamp
    global finish_timestamp
    global laptime
    global timepenalty
    global totaltime
    global attemptnr

    start_timestamp = None
    finish_timestamp = None
    laptime = None
    timepenalty = None
    totaltime = None
    attemptnr = None
    
    selected_team.set("")

    entry_start.delete(0,'end')
    selected_timestamp_start1.set(None)
    selected_timestamp_start2.set(None)
    canvas.itemconfig(start_timestamp_id,text="")

    entry_finish.delete(0,'end')
    selected_timestamp_finish1.set(None)
    selected_timestamp_finish2.set(None)
    canvas.itemconfig(finish_timestamp_id,text="")

    entry_laptime.delete(0,'end')
    canvas.itemconfig(laptime_id,text="")

    entry_timepenalty.delete(0,'end')
    canvas.itemconfig(timepenalty_id,text="")

    entry_attempt.delete(0,'end')
    canvas.itemconfig(totaltime_id,text="")

    for widget in window.winfo_children():
        if isinstance(widget, Radiobutton):
            widget.destroy()

    return   

def update_devices():
    combo_start1['values'] = devices
    combo_start2['values'] = devices
    combo_finish1['values'] = devices
    combo_finish2['values'] = devices 

def update_timestamps():
    for widget in window.winfo_children():
        if isinstance(widget, Radiobutton):
            widget.destroy()
       
    for i,timestamp in enumerate(start1_timestamps):
            radiobutton = Radiobutton(
                window,
                text=timestamp.time(),
                variable=selected_timestamp_start1,
                value=timestamp,
                command=partial(update_start_timestamp,None)
            )
            radiobutton.place(x=115.0, y=468.0+22*i)

    for i,timestamp in enumerate(start2_timestamps):
        radiobutton = Radiobutton(
            window,
            text=timestamp.time(),
            variable=selected_timestamp_start2,
            value=timestamp,
            command=partial(update_start_timestamp,None)
        )
        radiobutton.place(x=115.0, y=571.0+22*i)
    
    for i,timestamp in enumerate(finish1_timestamps):
        radiobutton = Radiobutton(
            window,
            text=timestamp.time(),
            variable=selected_timestamp_finish1,
            value=timestamp,
            command=partial(update_finish_timestamp,None)
        )
        radiobutton.place(x=115.0, y=679.0+22*i)

    for i,timestamp in enumerate(finish2_timestamps):
        radiobutton = Radiobutton(
            window,
            text=timestamp.time(),
            variable=selected_timestamp_finish2,
            value=timestamp,
            command=partial(update_finish_timestamp,None)
        )
        radiobutton.place(x=115.0, y=781.0+22*i)

def update_status(button):
    global status
    status = button

    if button:
        canvas.itemconfig(status_id,text="Active",fill="#00FF19")
    else:
        canvas.itemconfig(status_id,text="Inactive",fill="#FF0000")
        
def build_gui():    
    image_image_1 = PhotoImage(
        file=relative_to_assets("image_2.png"))
    image_1 = canvas.create_image(
        690.0,
        449.0,
        image=image_image_1
    )
    canvas.lower(image_1)

    update_timestamps()

    # challenges combobox
    global combo_challenge
    combo_challenge = ttk.Combobox(window, textvariable=selected_challenge, values=challenges_list)
    combo_challenge.place(x=80, y=206, width=164, height=41)
    combo_challenge["state"] = "readonly"
    combo_challenge.bind("<<ComboboxSelected>>", update_challenge)    

    # teams combobox
    combo_teams = ttk.Combobox(window, textvariable=selected_team, values=teams_list)
    combo_teams.place(x=406.0, y=206.0, width=271.0, height=41.0)
    combo_teams["state"] = "readonly"
    combo_teams.bind("<<ComboboxSelected>>", update_team)

    # devices
    global combo_start1
    combo_start1 = ttk.Combobox(window, textvariable=start1_selected, values=devices)
    combo_start1.place(x=1002.0, y=206.0, width=194.0, height=33.0)
    combo_start1["state"] = "readonly"
    combo_start1.bind("<<ComboboxSelected>>", lambda event: start1_timestamps.clear())

    global combo_start2
    combo_start2 = ttk.Combobox(window, textvariable=start2_selected, values=devices)
    combo_start2.place(x=1002.0, y=250.0, width=194.0, height=33.0)
    combo_start2["state"] = "readonly"
    combo_start2.bind("<<ComboboxSelected>>", lambda event: start2_timestamps.clear())

    global combo_finish1
    combo_finish1 = ttk.Combobox(window, textvariable=finish1_selected, values=devices)
    combo_finish1.place(x=1002.0, y=298.0, width=194.0, height=33.0)
    combo_finish1["state"] = "readonly"
    combo_finish1.bind("<<ComboboxSelected>>", lambda event: finish1_timestamps.clear())

    global combo_finish2
    combo_finish2 = ttk.Combobox(window, textvariable=finish2_selected, values=devices)
    combo_finish2.place(  x=1002.0, y=338.0, width=194.0, height=33.0)
    combo_finish2["state"] = "readonly"
    combo_finish2.bind("<<ComboboxSelected>>", lambda event: finish2_timestamps.clear())
 


    global penalty_id
    penalty_id = canvas.create_text(
        165.0,
        371.0,
        anchor="nw",
        text="",
        fill="#000000",
        font=("Inter SemiBold", 22 * -1)
    )

    global start_timestamp_id
    start_timestamp_id = canvas.create_text(
        395.0,
        525.0,
        anchor="nw",
        text="",
        fill="#000000",
        font=("Inter SemiBold", 20 * -1)
    )
    
    global finish_timestamp_id
    finish_timestamp_id = canvas.create_text(
        395.0,
        735.0,
        anchor="nw",
        text="",
        fill="#000000",
        font=("Inter SemiBold", 20 * -1)
    )

    global laptime_id
    laptime_id = canvas.create_text(
        590.0,
        655.0,
        anchor="nw",
        text="",
        fill="#000000",
        font=("Inter SemiBold", 22 * -1)
    )

    global timepenalty_id
    timepenalty_id = canvas.create_text(
        810.0,
        652.0,
        anchor="nw",
        text="",
        fill="#000000",
        font=("Inter SemiBold", 22 * -1)
    )

    global totaltime_id 
    totaltime_id = canvas.create_text(
        1020.0,
        652.0,
        anchor="nw",
        text="",
        fill="#000000",
        font=("Inter SemiBold", 22 * -1)
    )


    # manual imput start timestamp
    global entry_start
    entry_start_image = PhotoImage(
        file=relative_to_assets("entry_start.png"))
    entry_bg_7 = canvas.create_image(
        480.0,
        574.5,
        image=entry_start_image
    )
    entry_start = Entry(
        bd=0,
        bg="#D9D9D9",
        fg="#000716",
        highlightthickness=0
    )
    entry_start.place(
        x=438.0,
        y=562.0,
        width=84.0,
        height=23.0
    )

    button_man_start_image = PhotoImage(
        file=relative_to_assets("button_man_start.png"))
    button_man_start = Button(
        image=button_man_start_image,
        borderwidth=0,
        highlightthickness=0,
        command=lambda: update_start_timestamp(entry_start.get()),
        relief="flat"
    )
    button_man_start.place(
        x=522.0,
        y=562.0,
        width=33.0,
        height=25.0
    )


    # manual imput finish timestamp
    global entry_finish
    entry_finish_image = PhotoImage(
        file=relative_to_assets("entry_finish.png"))
    entry_bg_8 = canvas.create_image(
        480.0,
        784.5,
        image=entry_finish_image
    )
    entry_finish = Entry(
        bd=0,
        bg="#D9D9D9",
        fg="#000716",
        highlightthickness=0
    )
    entry_finish.place(
        x=438.0,
        y=772.0,
        width=84.0,
        height=23.0
    )

    button_man_finish_image = PhotoImage(
        file=relative_to_assets("button_man_finish.png"))
    button_man_finish = Button(
        image=button_man_finish_image,
        borderwidth=0,
        highlightthickness=0,
        command=lambda: update_finish_timestamp(entry_finish.get()),
        relief="flat"
    )
    button_man_finish.place(
        x=522.0,
        y=772.0,
        width=33.0,
        height=25.0
    )


    # manual input lap time
    global entry_laptime
    entry_laptime_image = PhotoImage(
        file=relative_to_assets("entry_laptime.png"))
    entry_bg_9 = canvas.create_image(
        672.0,
        699.5,
        image=entry_laptime_image
    )
    entry_laptime = Entry(
        bd=0,
        bg="#D9D9D9",
        fg="#000716",
        highlightthickness=0
    )
    entry_laptime.place(
        x=630.0,
        y=687.0,
        width=84.0,
        height=23.0
    )
    
    button_man_laptime_image = PhotoImage(
        file=relative_to_assets("button_man_laptime.png"))
    button_man_laptime = Button(
        image=button_man_laptime_image,
        borderwidth=0,
        highlightthickness=0,
        command=lambda: update_laptime(entry_laptime.get()),
        relief="flat"
    )
    button_man_laptime.place(
        x=714.0,
        y=687.0,
        width=33.0,
        height=25.0
    )

    
    # input attempt number
    global entry_attempt
    entry_attempt_image = PhotoImage(
        file=relative_to_assets("entry_attempt.png"))
    entry_bg_10 = canvas.create_image(
        668.0,
        558.5,
        image=entry_attempt_image
    )
    entry_attempt = Entry(
        bd=0,
        bg="#D9D9D9",
        fg="#000716",
        highlightthickness=0
    )
    entry_attempt.place(
        x=626.0,
        y=546.0,
        width=84.0,
        height=23.0
    )

    button_attempt_image = PhotoImage(
        file=relative_to_assets("button_attempt.png"))
    button_attempt = Button(
        image=button_attempt_image,
        borderwidth=0,
        highlightthickness=0,
        command=update_attemptnr,
        relief="flat"
    )
    button_attempt.place(
        x=710.0,
        y=546.0,
        width=33.0,
        height=25.0
    )


    # input hats down
    global entry_timepenalty
    entry_timepenalty_image = PhotoImage(
        file=relative_to_assets("entry_timepenalty.png"))
    entry_bg_11 = canvas.create_image(
        833.0,
        558.5,
        image=entry_timepenalty_image
    )
    entry_timepenalty = Entry(
        bd=0,
        bg="#D9D9D9",
        fg="#000716",
        highlightthickness=0
    )
    entry_timepenalty.place(
        x=791.0,
        y=546.0,
        width=84.0,
        height=23.0
    )

    button_timepenalty_image = PhotoImage(
        file=relative_to_assets("button_timepenalty.png"))
    button_timepenalty = Button(
        image=button_timepenalty_image,
        borderwidth=0,
        highlightthickness=0,
        command=update_timepenalty,
        relief="flat"
    )
    button_timepenalty.place(
        x=875.0,
        y=546.0,
        width=33.0,
        height=25.0
    )

    # input energy
    global entry_energy
    entry_energy_image = PhotoImage(
        file=relative_to_assets("entry_timepenalty.png"))
    entry_bg_12 = canvas.create_image(
        833.0,
        795.0,
        image=entry_energy_image
    )
    entry_energy = Entry(
        bd=0,
        bg="#D9D9D9",
        fg="#000716",
        highlightthickness=0
    )
    entry_energy.place(
        x=791.0,
        y=781.5,
        width=84.0,
        height=23.0
    )

    button_energy_image = PhotoImage(
        file=relative_to_assets("button_timepenalty.png"))
    button_energy = Button(
        image=button_energy_image,
        borderwidth=0,
        highlightthickness=0,
        command=update_timepenalty,
        relief="flat"
    )
    button_energy.place(
        x=875.0,
        y=781.5,
        width=33.0,
        height=25.0
    )


    # activate button
    button_activate_imga = PhotoImage(
    file=relative_to_assets("button_activate.png"))
    button_activate = Button(
        image=button_activate_imga,
        borderwidth=0,
        highlightthickness=0,
        command=lambda: update_status(True),
        relief="flat"
    )
    button_activate.place(
        x=992.0,
        y=395.0,
        width=99.0,
        height=32.0
    )

    # deactivate button
    button_deactivate_image = PhotoImage(
        file=relative_to_assets("button_deactivate.png"))
    button_deactivate = Button(
        image=button_deactivate_image,
        borderwidth=0,
        highlightthickness=0,
        command=lambda: update_status(False),
        relief="flat"
    )
    button_deactivate.place(
        x=1107.0,
        y=395.0,
        width=99.0,
        height=32.0
    )

    global status_id
    status_id = canvas.create_text(
        881.0,
        400.0,
        anchor="nw",
        text="Active",
        fill="#00FF19",
        font=("Inter SemiBold", 18 * -1)
    )

    # confirm button
    button_confirm_image = PhotoImage(
        file=relative_to_assets("button_confirm.png"))
    button_confirm = Button(
        image=button_confirm_image,
        borderwidth=0,
        highlightthickness=0,
        command=confirm,
        relief="flat"
    )
    button_confirm.place(
        x=1036.0,
        y=716.0,
        width=99.0,
        height=32.0
    )


    # decline button
    button_decline_image = PhotoImage(
        file=relative_to_assets("button_decline.png"))
    button_decline = Button(
        image=button_decline_image,
        borderwidth=0,
        highlightthickness=0,
        command=decline,
        relief="flat"
    )
    button_decline.place(
        x=1036.0,
        y=581.0,
        width=99.0,
        height=32.0
    )


    window.resizable(True, True)
    loadConfig()
    window.mainloop()



def on_connect(client, userdata, flags, rc):
    client.subscribe("esp32/timestamp",qos=2)
    client.subscribe("clients",qos=2)

def on_message(client, userdata, message):
    payload = message.payload.decode("utf-8")
    if message.topic == "esp32/timestamp" and status:
        data_json = json.loads(payload)
       
        if data_json["esp_id"] == start1_selected.get():
            start1_timestamps.insert(0,parser.isoparse(data_json['timestamp']))
            if len(start1_timestamps) == 5:
                start1_timestamps.pop(4)
                

        if data_json["esp_id"] == start2_selected.get():  
            start2_timestamps.insert(0,parser.isoparse(data_json["timestamp"]))
            if len(start2_timestamps) == 5:
                start2_timestamps.pop(4)

        if data_json["esp_id"] == finish1_selected.get():
            finish1_timestamps.insert(0,parser.isoparse(data_json["timestamp"]))
            if len(finish1_timestamps) == 5:
                finish1_timestamps.pop(4)
            
        if data_json["esp_id"] == finish2_selected.get():
            finish2_timestamps.insert(0,parser.isoparse(data_json["timestamp"]))
            if len(finish2_timestamps) == 5:
                finish2_timestamps.pop(4)

        update_timestamps()


    elif message.topic == "clients":
        if payload not in devices:
            devices.append(payload)
            update_devices()

def setup_mqtt():
    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        client.connect(SERVER_IP, MQTT_PORT, 60)
        client.loop_start()
    except:
        messagebox.showerror('Error',"Couldn't connect to MQTT-Server.")
        sys.exit()

setup_mariadb()

setup_mqtt()

build_gui()






