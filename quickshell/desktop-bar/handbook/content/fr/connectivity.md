# WiFi, Bluetooth et mode avion

Ouvrez Paramètres > Connexions et choisissez Wi-Fi ou Bluetooth. Les icônes de la barre ouvrent des panneaux rapides pour les mêmes appareils. Leur ouverture ne change pas le moteur réseau et ne déconnecte rien.

## Se connecter au Wi-Fi

Ouvrez Paramètres > Connexions > Wi-Fi, activez Wi-Fi et choisissez un réseau dans Autres réseaux. Saisissez son mot de passe si demandé. Rechercher relance la recherche. Réseau connecté montre la connexion actuelle ; Réseaux connus conserve les réseaux enregistrés, même hors ligne. Déconnecter termine la connexion ; Oublier retire un réseau enregistré après confirmation. La progression et les erreurs apparaissent à côté du réseau.

La partie supérieure indique état, ping, bande WiFi, adresse IP et passerelle. Le partage QR utilise un mot de passe WiFi fourni et garde l’image en mémoire. Les identifiants d’entreprise ne sont pas partagés sous forme de QR de réseau personnel.

Les réseaux d’entreprise acceptent PEAP/MSCHAPv2 et TTLS/PAP. Demandez à l’administrateur nom d’utilisateur, certificat d’autorité et domaine du serveur d’authentification. Ne désactivez pas la validation du certificat. Les autres méthodes exigent une configuration avancée. Voir [Services réseau](handbook:network-backends).

Choisissez le moteur WiFi dans Paramètres > Connexions > Wi-Fi > Moteur WiFi ; Walker > Paramètres > Périphériques > Connexions > Moteur de réseau reste une alternative. Lisez [Services réseau](handbook:network-backends) avant de changer. Le choix s’applique après redémarrage sans couper la connexion actuelle.

## Associer un appareil Bluetooth

Ouvrez Paramètres > Connexions > Bluetooth et activez Bluetooth. Choisissez Rechercher, puis un appareil à associer et connecter. Appareils connectés, Appareils connus et Autres appareils sont des listes séparées. Afficher les appareils sans nom aide à trouver un appareil anonyme. Déconnecter conserve l’association ; Oublier la retire. La recherche s’arrête après 20 secondes, en quittant la page ou en fermant le panneau.

L’association peut nécessiter un PIN ou un agent de confirmation. Le bureau actuel utilise Blueman pour ces dialogues. Reconnecter un appareil déjà associé ne prouve pas qu’une nouvelle association fonctionne. Conservez cet agent jusqu’à avoir testé une association par PIN ou confirmation. La couverture de l’agent sur les nouvelles installations reste à vérifier.

## Mode avion

Centre de contrôle > Général bloque WiFi et Bluetooth avec rfkill. Le désactiver ne rétablit que les radios qu’il a lui-même bloquées. Les blocages matériels ou externes ne sont pas annulés silencieusement. Activez une radio individuellement si nécessaire.

## VPN

Walker n’a pas de menu VPN. WireGuard et NetworkManager VPN sont prévus sous forme de plugins (Installer > Plugins). Les entrées Tailscale se trouvent dans Walker > Paramètres > Périphériques > Streaming > Accéder à ce PC à distance ; voir [Accès à distance](handbook:remote-access).
