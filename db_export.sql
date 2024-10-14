-- phpMyAdmin SQL Dump
-- version 5.2.1deb1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Oct 14, 2024 at 03:01 PM
-- Server version: 10.11.6-MariaDB-0+deb12u1
-- PHP Version: 8.2.24

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `Zeitmessung`
--

-- --------------------------------------------------------

--
-- Table structure for table `challenges`
--

CREATE TABLE `challenges` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL,
  `penalty` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `challenges`
--

INSERT INTO `challenges` (`id`, `name`, `penalty`) VALUES
(1, 'skidpad', 2),
(2, 'slalom', 2),
(3, 'beschleunigung', 0),
(4, 'dauerlauf', 2);

-- --------------------------------------------------------

--
-- Table structure for table `challenges_best_attempts`
--

CREATE TABLE `challenges_best_attempts` (
  `id` int(11) NOT NULL,
  `team_id` int(11) DEFAULT NULL,
  `challenge_id` int(11) NOT NULL,
  `time` float NOT NULL,
  `power` float DEFAULT NULL,
  `energy` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `challenges_best_attempts`
--

INSERT INTO `challenges_best_attempts` (`id`, `team_id`, `challenge_id`, `time`, `power`, `energy`) VALUES
(888, 1, 1, 3600, NULL, NULL),
(889, 2, 1, 30, NULL, NULL),
(890, 3, 1, 3, NULL, NULL),
(891, 1, 2, 18000, NULL, NULL),
(892, 2, 2, 3600, NULL, NULL),
(893, 3, 2, 1200, NULL, NULL),
(894, 1, 3, 3600, 1234.12, NULL),
(895, 2, 3, 14400, 32423.7, NULL),
(896, 3, 3, 3600, 432, NULL),
(897, 1, 4, 17902, NULL, 432),
(898, 2, 4, 3663, NULL, 432.432),
(899, 3, 4, 3606, NULL, 5432);

-- --------------------------------------------------------

--
-- Table structure for table `challenges_data`
--

CREATE TABLE `challenges_data` (
  `id` int(11) NOT NULL,
  `tea_id` int(11) NOT NULL,
  `cmp_id` int(11) NOT NULL,
  `attempt_nr` int(11) NOT NULL,
  `starttime` datetime(6) DEFAULT NULL,
  `stoptime` datetime(6) DEFAULT NULL,
  `timepenalty` float DEFAULT NULL,
  `time` float NOT NULL,
  `power` float DEFAULT NULL,
  `energy` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `challenges_data`
--

INSERT INTO `challenges_data` (`id`, `tea_id`, `cmp_id`, `attempt_nr`, `starttime`, `stoptime`, `timepenalty`, `time`, `power`, `energy`) VALUES
(2, 1, 1, 1, '2024-10-04 05:00:00.000000', '2024-10-04 06:00:00.000000', NULL, 3600, NULL, NULL),
(3, 1, 1, 2, '2024-10-07 12:00:00.000000', '2024-10-07 13:00:00.000000', 3, 3603, NULL, NULL),
(4, 1, 2, 3, '2024-10-07 01:00:00.000000', '2024-10-07 06:00:00.000000', 0, 18000, NULL, NULL),
(5, 2, 2, 1, '2024-10-07 01:00:00.000000', '2024-10-07 02:00:00.000000', 0, 3600, NULL, NULL),
(6, 3, 2, 1, '2024-10-07 01:00:00.000000', '2024-10-07 01:20:00.000000', 0, 1200, NULL, NULL),
(7, 2, 1, 2, '2024-10-07 10:00:30.000000', '2024-10-07 10:01:00.000000', 0, 30, NULL, NULL),
(11, 1, 4, 5, '2024-10-13 04:05:44.000000', '2024-10-13 09:04:02.000000', 4, 17902, NULL, 432),
(12, 1, 3, 1, '2024-10-13 11:00:00.000000', '2024-10-13 12:00:00.000000', 0, 3600, 1234.12, NULL),
(13, 2, 4, 1, '2024-10-13 00:00:00.000000', '2024-10-13 01:01:01.000000', 2, 3663, NULL, 432.432),
(14, 2, 3, 1, '2024-10-13 00:00:00.000000', '2024-10-13 04:00:00.000000', 0, 14400, 32423.7, NULL),
(15, 3, 3, 1, '2024-10-13 04:00:00.000000', '2024-10-13 05:00:00.000000', 0, 3600, 432, NULL),
(16, 3, 4, 2, '2024-10-13 11:00:00.000000', '2024-10-13 12:00:00.000000', 6, 3606, NULL, 5432),
(17, 3, 1, 1, '2024-10-13 11:00:12.000000', '2024-10-13 11:00:13.000000', 2, 3, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `leaderboard`
--

CREATE TABLE `leaderboard` (
  `id` int(11) NOT NULL,
  `team_id` int(11) NOT NULL,
  `points` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `leaderboard`
--

INSERT INTO `leaderboard` (`id`, `team_id`, `points`) VALUES
(139, 1, 861.524),
(140, 2, 298.679),
(141, 3, 2340.98);

-- --------------------------------------------------------

--
-- Table structure for table `raw_data`
--

CREATE TABLE `raw_data` (
  `id` int(11) NOT NULL,
  `esp_id` text NOT NULL,
  `timestamp` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `teams`
--

CREATE TABLE `teams` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL,
  `vehicle_weight` float NOT NULL,
  `driver_weight` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `teams`
--

INSERT INTO `teams` (`id`, `name`, `vehicle_weight`, `driver_weight`) VALUES
(1, 'Team 1', 60, 70),
(2, 'Team 2', 100, 50),
(3, 'Team 3', 70.5344, 65.323);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `challenges`
--
ALTER TABLE `challenges`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `challenges_best_attempts`
--
ALTER TABLE `challenges_best_attempts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_challenges_best_attempts_team_id` (`team_id`),
  ADD KEY `ix_challenges_best_attempts_id` (`id`),
  ADD KEY `challenge_id` (`challenge_id`);

--
-- Indexes for table `challenges_data`
--
ALTER TABLE `challenges_data`
  ADD PRIMARY KEY (`id`),
  ADD KEY `tea_id` (`tea_id`),
  ADD KEY `cmp_id` (`cmp_id`),
  ADD KEY `ix_challenges_data_id` (`id`);

--
-- Indexes for table `leaderboard`
--
ALTER TABLE `leaderboard`
  ADD PRIMARY KEY (`id`),
  ADD KEY `team_id` (`team_id`);

--
-- Indexes for table `raw_data`
--
ALTER TABLE `raw_data`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_raw_data_id` (`id`);

--
-- Indexes for table `teams`
--
ALTER TABLE `teams`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `challenges`
--
ALTER TABLE `challenges`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `challenges_best_attempts`
--
ALTER TABLE `challenges_best_attempts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=900;

--
-- AUTO_INCREMENT for table `challenges_data`
--
ALTER TABLE `challenges_data`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- AUTO_INCREMENT for table `leaderboard`
--
ALTER TABLE `leaderboard`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=142;

--
-- AUTO_INCREMENT for table `raw_data`
--
ALTER TABLE `raw_data`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `teams`
--
ALTER TABLE `teams`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `challenges_data`
--
ALTER TABLE `challenges_data`
  ADD CONSTRAINT `challenges_data_ibfk_1` FOREIGN KEY (`tea_id`) REFERENCES `teams` (`id`),
  ADD CONSTRAINT `challenges_data_ibfk_2` FOREIGN KEY (`cmp_id`) REFERENCES `challenges` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
