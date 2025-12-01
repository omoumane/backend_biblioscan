-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1
-- Généré le : lun. 01 déc. 2025 à 14:17
-- Version du serveur : 10.4.32-MariaDB
-- Version de PHP : 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `bibliodb`
--

-- --------------------------------------------------------

--
-- Structure de la table `bibliotheques`
--

CREATE TABLE `bibliotheques` (
  `biblio_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `nb_lignes` int(11) NOT NULL,
  `nb_colonnes` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `bibliotheques`
--

INSERT INTO `bibliotheques` (`biblio_id`, `user_id`, `nom`, `nb_lignes`, `nb_colonnes`) VALUES
(1, 1, 'Bibliothèque principale', 3, 4),
(2, 2, 'Bibliothèque 12', 5, 10),
(3, 2, 'Bibliothèque 112', 2, 1),
(4, 2, 'Bibliothèque Reda', 2, 1),
(5, 2, 'Bibliothèque Reda---', 2, 1),
(6, 2, 'Bibliothèque Principale hhhh', 5, 10),
(7, 5, 'BIB_77', 1, 1),
(8, 6, 'hassan', 5, 5),
(13, 6, 'ttt', 3, 3),
(15, 6, 'oussama', 1, 1),
(16, 6, 'nihal', 6, 6),
(17, 10, 'gs', 5, 2);

-- --------------------------------------------------------

--
-- Structure de la table `livres`
--

CREATE TABLE `livres` (
  `livre_id` int(11) NOT NULL,
  `biblio_id` int(11) NOT NULL,
  `titre` varchar(255) NOT NULL,
  `auteur` varchar(150) DEFAULT NULL,
  `date_pub` varchar(50) DEFAULT NULL,
  `position_ligne` int(11) NOT NULL,
  `position_colonne` int(11) NOT NULL,
  `couverture_url` text DEFAULT NULL,
  `correction_manuelle` tinyint(1) DEFAULT 0,
  `isbn` varchar(32) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `livres`
--

INSERT INTO `livres` (`livre_id`, `biblio_id`, `titre`, `auteur`, `date_pub`, `position_ligne`, `position_colonne`, `couverture_url`, `correction_manuelle`, `isbn`) VALUES
(22, 8, 'Le Diable au Corps', 'Raymond Radiguet', '2022-10-05', 2, 3, 'http://books.google.com/books/content?id=j9mSEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, '9782322458523'),
(23, 8, 'Proust Johnson désajeuies des Cu teules', 'Inconnu', NULL, 2, 3, NULL, 0, NULL),
(24, 8, '# Mnémoires d\'Outre-Tombe n\'est pas présent, mais il semble qu\'il y ait une erreur d\'OCR. \n# Il est possible que le texte soit : \n# Mnémoires, mais le début du texte semble être \"Mnbreno\" qui', 'Inconnu', NULL, 2, 3, NULL, 0, NULL),
(25, 8, 'L\'Enfant qui disait n\'importe quoi', 'André Dhôtel', '1978', 2, 3, NULL, 0, NULL),
(26, 8, 'La fin de l\'histoire', 'Luis Sepulveda', '2020-04-23', 2, 3, 'http://books.google.com/books/content?id=2dHXDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, '9791022606059'),
(27, 13, '', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(28, 13, 'District of Columbia Appropriations for 1999', 'United States. Congress. House. Committee on Appropriations. Subcommittee on District of Columbia Appropriations', '1999', 1, 1, 'http://books.google.com/books/content?id=Iv1LboPBHg0C&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, NULL),
(29, 13, 'Grosse faim', 'John Fante', '2023-07-20', 1, 1, 'http://books.google.com/books/content?id=6rbIEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, '9782264083883'),
(30, 13, 'Allan Rar Qtlu n\'est pas corrigé car il n\'y a pas d\'erreur évidente de reconnaissance de caractères. Cependant, si l\'on suppose que \"Qtlu\" pourrait être une erreur d\'OCR pour \"Quel\", cela donnerait \"All', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(31, 13, 'Oeuvres de André Gide', 'André Gide', '1927', 1, 1, NULL, 0, NULL),
(32, 13, 'Le Diable au Corps', 'Raymond Radiguet', '2022-10-05', 1, 1, 'http://books.google.com/books/content?id=j9mSEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, '9782322458523'),
(33, 13, 'Do Alombe des jeunes filles ti teus Praist', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(34, 13, '', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(35, 13, 'Luis Sepúlveda, Le Vieux qui lisait des romans d\'amour', 'Léo Lamarche, Luis Sepúlveda', '2007', 1, 1, NULL, 0, NULL),
(36, 13, 'La fin de l\'histoire', 'Luis Sepulveda', '2020-04-23', 1, 1, 'http://books.google.com/books/content?id=2dHXDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, '9791022606059'),
(37, 13, '1229Y', 'Inconnu', NULL, 1, 1, 'http://books.google.com/books/content?id=TbGrCgAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, NULL),
(38, 13, 'Il n\'y a pas de texte à corriger. Le texte fourni est un pourcentage et une liste de tâches, sans contenu à corriger. \n\n93 %\nTâches :\n1) Corrige uniquement les erreurs d\'OCR évidentes (lettres/', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(44, 15, 'La peau de Chagrin', 'Honoré de Balzac', '1891', 1, 1, 'http://books.google.com/books/content?id=dtoTAAAAYAAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, NULL),
(45, 15, 'Alcools', 'Guillaume Apollinaire', NULL, 1, 1, NULL, 0, NULL),
(46, 15, 'Alcool, drogues... et création artistique ?', 'Nicolas Pinon', '2013-11-13', 1, 1, 'http://books.google.com/books/content?id=4iteAgAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, '9782875582430'),
(47, 15, 'Patrunamé eFace= Clajauquca Lalp?lace Gallimard Annlle G naux ClassicDlycle BFLIN (SHARESFEARE \n\ndevient :\nPatronyme eFace= Clajauquca Lalplace Gallimard Anne G naux', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(48, 15, 'Oeuvres complètes de Shakespeare', 'William Shakespeare', '1968', 1, 1, NULL, 0, NULL),
(49, 15, 'MYACBEII devient Balzac, DENIS DIDLROT devient Denis Diderot, Lalelgiens devient Les Égliens n\'est pas évident mais on peut penser à \"Les Égarements\" ou \"Les Élégies\" mais', 'Denis Diderot', NULL, 1, 1, NULL, 0, NULL),
(50, 8, 'othman', 'othmane', '2011', 2, 2, NULL, 0, NULL),
(51, 16, 'Alcools', 'Guillaume Apollinaire', '2021-05-27', 1, 1, 'http://books.google.com/books/content?id=BVEwEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, '9782322414369'),
(52, 16, 'Théâtre complet de Beaumarchais: La folle journée, ou, Le mariage de Figaro', 'Pierre Augustin Caron de Beaumarchais', '1870', 1, 1, 'http://books.google.com/books/content?id=vbwzAQAAIAAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, NULL),
(53, 16, 'Le Portrait de Dorian Gray', 'Oscar Wilde, Michèle Zachayus', '2023-10-13', 1, 1, 'http://books.google.com/books/content?id=Lo3cEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, '9782957879038'),
(54, 16, 'L\'Ingénu', 'Voltaire,, Ligaran,', '2015-02-04', 1, 1, 'http://books.google.com/books/content?id=va6iBgAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, '9782335012484'),
(55, 16, 'La Peau de chagrin', 'Honoré de Balzac', NULL, 1, 1, NULL, 0, NULL),
(56, 15, '', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(57, 15, '', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(58, 8, '', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(59, 8, 'Sudoku Classique 9x9 - Facile à Diabolique - Volume 1 - 276 Grilles', 'Nick Snels', '2015-03-14', 1, 1, 'http://books.google.com/books/content?id=6BoQCwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, '9781508873204'),
(60, 8, 'Kieli, Vol. 9 (light novel)', 'Yukako Kabei', '2018-03-27', 1, 1, 'http://books.google.com/books/content?id=fBg1DwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api', 0, '9781975301002'),
(61, 8, '', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(62, 8, '', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(63, 8, '', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(64, 8, '', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(65, 8, '', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(66, 8, '', 'Inconnu', NULL, 1, 1, NULL, 0, NULL),
(67, 8, '', 'Inconnu', NULL, 1, 1, NULL, 0, NULL);

-- --------------------------------------------------------

--
-- Structure de la table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `username` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `prenom` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `users`
--

INSERT INTO `users` (`user_id`, `username`, `password`, `nom`, `prenom`) VALUES
(1, 'omoumane', '$2y$10$xycC46FDVNO2J3acKlpBPOoVnLVb9heAqat6/exDEVm5rT65xnCB6', '', ''),
(2, 'othmane', '$2y$10$NyYkgoCoS3GZ1D4AgsdHL.dAJ2RVprR6C6beMkzMctlL6shU9Gf0e', '', ''),
(3, 'omoumane1', '$2y$10$0da/pJCQp9DEXwjJode/UumWDOTVtFh7CKe5.UdUvU0Ve8ykeDth.', 'M', 'Othm'),
(4, 'raha', '$2y$10$COF/MhMvy8OzLkilLCFocuxu3qIvRa/r3xM7jmH7cEDwbqfzEqWGm', 'reda', 'abdellaoui'),
(5, 'rabdel', '$2y$10$W0SkfBEviggYcgszrT8qJun38RPdd4IEcs6cBxRGFA/Od8exHjvzi', 'reda', 'abdellaoui'),
(6, 'abdell', '$2y$10$7jyvPuRY2i6BX.kZJ2eJje4hIvZl5p/WDbZmtZQGWFtduvTsyIANq', 'reda', 'abdellaoui'),
(7, 'reda', '$2y$10$r.rq6NcPxQCz9r7wvMBybe1NTcoyI971IQlEBVjNQMxcEJYQYv48y', 'reda', 'reda'),
(8, 'oussama', '$2y$10$7qCkwhMFwsgSKuHn6ntupu2C4tKnovIpPchPSjbuUfIbR7rmDWn2G', 'oussama', 'oussama'),
(9, 'kcxjck', '$2y$10$txJUg4MxO50GQW5PNJJfyO9BhW9e6yZoR5.74OgIeCpBaUpSqMPQC', 'fj k', 'cjfifi'),
(10, 'red', '$2y$10$qChRoDop5tG1gTed5e8FdOgmnz7sJL/SEJ80BDHIgF5qo.7794RIa', 'red', 'red');

-- --------------------------------------------------------

--
-- Structure de la table `user_tokens`
--

CREATE TABLE `user_tokens` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `token` varchar(255) NOT NULL,
  `expires_at` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `user_tokens`
--

INSERT INTO `user_tokens` (`id`, `user_id`, `token`, `expires_at`) VALUES
(124, 6, '86af4651cffc423f056bd6413f69bdc8ac369ed513b6a82a5a072f5fbf7c4b77', '2025-12-01 11:02:13');

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `bibliotheques`
--
ALTER TABLE `bibliotheques`
  ADD PRIMARY KEY (`biblio_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Index pour la table `livres`
--
ALTER TABLE `livres`
  ADD PRIMARY KEY (`livre_id`),
  ADD KEY `biblio_id` (`biblio_id`);

--
-- Index pour la table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Index pour la table `user_tokens`
--
ALTER TABLE `user_tokens`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `token` (`token`),
  ADD KEY `user_id` (`user_id`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `bibliotheques`
--
ALTER TABLE `bibliotheques`
  MODIFY `biblio_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- AUTO_INCREMENT pour la table `livres`
--
ALTER TABLE `livres`
  MODIFY `livre_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=68;

--
-- AUTO_INCREMENT pour la table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT pour la table `user_tokens`
--
ALTER TABLE `user_tokens`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=125;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `bibliotheques`
--
ALTER TABLE `bibliotheques`
  ADD CONSTRAINT `bibliotheques_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `livres`
--
ALTER TABLE `livres`
  ADD CONSTRAINT `livres_ibfk_1` FOREIGN KEY (`biblio_id`) REFERENCES `bibliotheques` (`biblio_id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `user_tokens`
--
ALTER TABLE `user_tokens`
  ADD CONSTRAINT `user_tokens_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
