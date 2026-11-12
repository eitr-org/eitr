# Informations, médias et notifications

Les cartes de notification affichent la date et l’heure locales d’arrivée sous le titre, dans les popups comme dans l’historique. Ces horaires sont conservés uniquement pendant la session.

## Consulter les informations système

Ouvrez Paramètres > À propos pour la version d’Eitr, le nom de code, le canal, le noyau et la licence, ainsi que le processeur, la carte graphique, la carte mère, la mémoire installée et chaque disque connecté avec sa capacité. La vue Système montre votre profil, l’utilisation actuelle du matériel et la vitesse du réseau (téléchargement et envoi). Pour les détails matériels, l’utilisation de l’IA et la météo, cliquez sur les icônes de la barre ; Walker les trouve aussi par nom.

**Matériel** indique CPU, GPU, RAM et stockage du disque contenant `/`. Les autres disques ne sont pas additionnés à ce total. Les données manquantes des capteurs ou du GPU sont indiquées comme indisponibles.

Dans Paramètres > À propos, choisissez Emblème ou Runes sous « Logo À propos » pour modifier la page À propos du terminal. Le choix est enregistré sur cet ordinateur et utilise Emblème par défaut ; les deux suivent la couleur d’accent du thème actuel.


**Utilisation de l’IA** détecte les clients installés ou configurés. L’usage en cache apparaît d’abord ; actualiser ne lance ni connexion ni conversation. Les limites de chaque compte sont affichées ; les pourcentages indiquent la part d’une limite déjà utilisée. Claude, Codex, Grok et Antigravity ont des limites de forfait lisibles (Antigravity par groupe de modèles : Gemini, Claude & GPT et Argon) ; les assistants facturés à l’usage, comme Copilot CLI, OpenCode, Pi ou Gemini CLI avec une clé d’API, n’apparaissent pas.

Chaque fournisseur détecté possède sa propre section avec son forfait, ses limites et ses erreurs. Cliquez sur un titre pour replier ou déplier cette seule section. À la connexion, toutes sont repliées ; leur état est conservé pendant la session. Les longues listes défilent dans les limites de l’écran.

**Météo** utilise l’emplacement par défaut et permet des recherches temporaires de villes. La sélection temporaire prend fin à la fermeture du panneau. Escape efface d’abord la recherche avant de fermer ; les unités de température suivent l’emplacement, avec une unité alternative à côté.

## Calendrier et médias

Cliquez sur l’horloge ou la date pour ouvrir le calendrier. Il conserve six lignes de semaines et affiche la progression de l’année sous la grille. Naviguez avec précédent/suivant, Aujourd’hui, les flèches ou T. Si la barre est masquée, recherchez Calendrier dans Walker. Cliquez sur un jour pour voir ses rappels sous la grille ; le + à côté du jour ouvre ses projets sur place, avec un champ pour ajouter un rappel à une heure de ce jour, et la flèche de retour ramène au mois.

Cliquez sur l’égaliseur animé pour ouvrir le panneau Médias : la pochette entourée de barres qui suivent la musique, le morceau, ses paroles, précédent/lecture/suivant et le déplacement dans la piste si possible. Il disparaît sans lecteur compatible et exclut les réunions reconnues. L’égaliseur de la barre suit le son du système via un processus cava privé uniquement pendant la lecture et lorsque la zone est visible. Faites glisser l’égaliseur vers la gauche pour le remplacer par la ligne chantée ; faites glisser la ligne dans un sens ou l’autre pour le retrouver ; la pause ou un changement de morceau la conserve. Les paroles en ligne sont un réglage de la Barre de bureau (voir le chapitre Barre et espaces de travail).

## Notifications

**SUPER + N** ou la cloche ouvre le centre de notifications. Les notifications sont regroupées par application. La carte la plus récente est devant la pile ; développez-la pour voir les précédentes. Vous pouvez ignorer une carte, effacer un groupe ou tout effacer. Les popups forment aussi des piles par application, avec le message le plus récent devant.

Le survol suspend leur expiration. **SUPER + Alt + N** lance l’action principale de la notification la plus récente (comme un clic dessus), et **SUPER + Alt + Shift + N** la ferme. Une notification répétée (même application, titre et texte) remplace la précédente et affiche un compteur comme ×3 au lieu d’empiler une autre carte.

Les notifications ont une douce lueur intérieure dans la couleur d’accent du thème. Les critiques utilisent plutôt son rouge ; celles de faible priorité restent discrètes, sans lueur. Ne pas déranger masque les popups sans supprimer l’historique. Celui-ci reste en mémoire lors des rechargements de configuration, mais pas après le redémarrage du processus. Aucun contenu de notification n’est enregistré dans un journal.

Un clic sur une notification lance son action principale. Une notification sans action ouvre l’application qui l’a envoyée : sa fenêtre, ou pour herdr le terminal qui l’exécute, sur l’espace de travail et l’onglet indiqués par la notification. Chaque carte affiche l’icône de l’application quand elle en a une, sinon la cloche.

Les notifications apparaissent sur chaque écran. Désactivez Notifications sur chaque écran dans Paramètres > Notifications pour les garder sur l'écran principal. La même page propose Ne pas déranger et Notifications de plantage.
