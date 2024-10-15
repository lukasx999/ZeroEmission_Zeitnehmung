#!/usr/bin/env bash

set -euo pipefail

echo "this script is not finished, do not run it!"
exit 1

# NOTE: this script is not finished and needs proper testing!



# Only for 'Zeitmessung' table
function exec_sql_zeitmessung {
stmt=$1
mysql -u root -p -e "USE Zeitmessung; $stmt";
}


function exec_sql {
stmt=$1
mysql -u root -p -e $stmt;
}


sudo apt update
sudo apt upgrade
sudo apt install mariadb-server -y



input='n\nY\nKennwort1\nKennwort1\nY\nY\nY\nY'
echo -e $input | sudo mysql_secure_installation # INTERACTIVE



sed /etc/mysql/mariadb.conf.d/50-server.cnf 's/127.0.0.1/0.0.0.0/'


# SQL:
exec_sql "CREATE DATABASE Zeitmessung;"
exec_sql "CREATE USER 'mariadbclient'@'%' IDENTIFIED BY 'Kennwort1';"
exec_sql "GRANT ALL PRIVILEGES ON Zeitmessung.* TO 'mariadbclient'@'%';"
exec_sql "FLUSH PRIVILEGES;"

# TODO: REBOOT


sudo apt install phpmyadmin -y # INTERACTIVE
sudo apt install mosquitto -y
sudo systemctl enable mosquitto
sudo mosquitto_passwd -c /etc/mosquitto/credentials mqttclient # INTERACTIVE


contents="listener 1883\nallow_anonymous false\npassword_file /etc/mosquitto/credentials\n"
echo -e $contents > /etc/mosquitto/conf.d/local.conf

sudo systemctl restart mosquitto

# change mqtt and database configs

# TODO: rsync git repo
sudo mv /home/admin/01_RP-Zeitmessung /var/www
sudo chown -R admin:www-data /var/www/01_RP-Zeitmessung
sudo mv /var/www/01_RP-Zeitmessung/webserver.conf /etc/apache2/sites-available

mkdir /var/www/01_RP-Zeitmessung/logs # Error on 'systemctl restart apache2'



# DB:

CREATE TABLE teams (
id integer NOT NULL AUTO_INCREMENT,
name text NOT NULL,
vehicle_weight float NOT NULL,
driver_weight float NOT NULL,
PRIMARY KEY (id)
);



CREATE TABLE challenges (
id integer NOT NULL AUTO_INCREMENT,
name text NOT NULL,
penalty float NOT NULL,
PRIMARY KEY (id)
);




#/ auto generated on http server visit?
CREATE TABLE challenges_data (
id integer NOT NULL AUTO_INCREMENT,
tea_id integer NOT NULL,
cmp_id integer NOT NULL,
attempt_nr integer NOT NULL,
starttime datetime,
stoptime datetime,
timepenalty float,
time float NOT NULL,
power float,
energy float,
PRIMARY KEY (id)
);


# TODO: generate "challenges_best_attempts"
CREATE TABLE challenges_best_attempts (
id integer NOT NULL AUTO_INCREMENT,
challenge_id integer NOT NULL,
team_id integer NOT NULL,
time float NOT NULL,
power float,
energy float,
PRIMARY KEY (id)
);

CREATE TABLE leaderboard (
id integer NOT NULL AUTO_INCREMENT,
team_id integer NOT NULL,
points float,
PRIMARY KEY (id)
);

CREATE TABLE raw_data (
id integer NOT NULL AUTO_INCREMENT,
esp_id text NOT NULL,
timestamp datetime NOT NULL,
PRIMARY KEY (id)
);
#/


# SQL:
exec_sql_zeitmessung "INSERT INTO teams (name) VALUES ('Team 1'), ('Team 2'), ('Team 3');"
exec_sql_zeitmessung "INSERT INTO challenges (name, penalty) VALUES ('Challgende 1', 1.0), ('Challenge 2', 2.0);"
