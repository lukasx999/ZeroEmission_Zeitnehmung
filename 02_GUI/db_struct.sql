-- phpMyAdmin SQL Dump
-- version 5.2.1deb1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Erstellungszeit: 19. Okt 2024 um 14:37
-- Server-Version: 10.11.6-MariaDB-0+deb12u1
-- PHP-Version: 8.2.24

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Datenbank: `Zeitmessung`
--
CREATE DATABASE IF NOT EXISTS `Zeitmessung` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `Zeitmessung`;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `challenges`
--

CREATE TABLE `challenges` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL,
  `penalty` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Daten für Tabelle `challenges`
--

INSERT INTO `challenges` (`id`, `name`, `penalty`) VALUES
(1, 'Skidpad', 2),
(2, 'Slalom', 2),
(3, 'Acceleration', 0),
(4, 'Endurance', 2);

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `challenges_best_attempts`
--

CREATE TABLE `challenges_best_attempts` (
  `id` int(11) NOT NULL,
  `challenge_id` int(11) NOT NULL,
  `team_id` int(11) NOT NULL,
  `time` float NOT NULL,
  `power` float DEFAULT NULL,
  `energy` float DEFAULT NULL,
  `category` int(11) NOT NULL,
  `power_weight_ratio` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `challenges_data`
--

CREATE TABLE `challenges_data` (
  `id` int(11) NOT NULL,
  `tea_id` int(11) NOT NULL,
  `cmp_id` int(11) NOT NULL,
  `attempt_nr` int(11) NOT NULL,
  `starttime` datetime DEFAULT NULL,
  `stoptime` datetime DEFAULT NULL,
  `timepenalty` float DEFAULT NULL,
  `time` float NOT NULL,
  `power` float DEFAULT NULL,
  `energy` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `leaderboard`
--

CREATE TABLE `leaderboard` (
  `id` int(11) NOT NULL,
  `team_id` int(11) NOT NULL,
  `points` float DEFAULT NULL,
  `category` int(11) NOT NULL,
  `points_skidpad` float NOT NULL,
  `points_slalom` float NOT NULL,
  `points_acceleration` float NOT NULL,
  `points_endurance` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `raw_data`
--

CREATE TABLE `raw_data` (
  `id` int(11) NOT NULL,
  `esp_id` text NOT NULL,
  `timestamp` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `teams`
--

CREATE TABLE `teams` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL,
  `vehicle_weight` float NOT NULL,
  `driver_weight` float NOT NULL,
  `category` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indizes der exportierten Tabellen
--

--
-- Indizes für die Tabelle `challenges`
--
ALTER TABLE `challenges`
  ADD PRIMARY KEY (`id`);

--
-- Indizes für die Tabelle `challenges_best_attempts`
--
ALTER TABLE `challenges_best_attempts`
  ADD PRIMARY KEY (`id`);

--
-- Indizes für die Tabelle `challenges_data`
--
ALTER TABLE `challenges_data`
  ADD PRIMARY KEY (`id`);

--
-- Indizes für die Tabelle `leaderboard`
--
ALTER TABLE `leaderboard`
  ADD PRIMARY KEY (`id`);

--
-- Indizes für die Tabelle `raw_data`
--
ALTER TABLE `raw_data`
  ADD PRIMARY KEY (`id`);

--
-- Indizes für die Tabelle `teams`
--
ALTER TABLE `teams`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT für exportierte Tabellen
--

--
-- AUTO_INCREMENT für Tabelle `challenges`
--
ALTER TABLE `challenges`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT für Tabelle `challenges_best_attempts`
--
ALTER TABLE `challenges_best_attempts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT für Tabelle `challenges_data`
--
ALTER TABLE `challenges_data`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT für Tabelle `leaderboard`
--
ALTER TABLE `leaderboard`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT für Tabelle `raw_data`
--
ALTER TABLE `raw_data`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT für Tabelle `teams`
--
ALTER TABLE `teams`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

CREATE USER 'mariadbclient'@'%' IDENTIFIED BY 'Kennwort1';
GRANT ALL PRIVILEGES ON Zeitmessung.* TO 'mariadbclient'@'%';

FLUSH PRIVILEGES;


/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
