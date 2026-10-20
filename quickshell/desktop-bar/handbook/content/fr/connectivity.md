# WiFi, Bluetooth et mode avion

Ouvrez les icônes de la barre ou **Système > Connectivité**. Ouvrir un panneau ne change jamais le service réseau et ne déconnecte aucun appareil de lui-même.

## WiFi

Le panneau sépare réseaux connectés, connus et autres réseaux. Choisissez un réseau disponible pour vous connecter ; les champs de mot de passe masquent leur contenu. Les réseaux enregistrés indisponibles restent visibles sans faux pourcentage de signal. Déconnecter se trouve sur la ligne connectée ; oublier un réseau enregistré demande confirmation.

La partie supérieure indique état, ping, bande WiFi, adresse IP et passerelle. Le partage QR utilise un mot de passe WiFi fourni et garde l’image en mémoire. Les identifiants d’entreprise ne sont pas partagés sous forme de QR de réseau personnel.

Les réseaux d’entreprise acceptent PEAP/MSCHAPv2 et TTLS/PAP. Demandez à l’administrateur nom d’utilisateur, certificat d’autorité et domaine du serveur d’authentification. Ne désactivez pas la validation du certificat. Les autres méthodes exigent une configuration avancée. Voir [Services réseau](handbook:network-backends).

## Bluetooth

Activez ou désactivez l’adaptateur, recherchez, associez, connectez, déconnectez ou oubliez des appareils. Les appareils connectés, connus et nouvellement détectés forment des groupes distincts. Une recherche lancée par le panneau s’arrête après 20 secondes ou à sa fermeture.

L’association peut nécessiter un PIN ou un agent de confirmation. Le bureau actuel utilise Blueman pour ces dialogues. Reconnecter un appareil déjà associé ne prouve pas qu’une nouvelle association fonctionne. Conservez cet agent jusqu’à avoir testé une association par PIN ou confirmation. La couverture de l’agent sur les nouvelles installations reste à vérifier.

## Mode avion

Centre de contrôle > Général bloque WiFi et Bluetooth avec rfkill. Le désactiver ne rétablit que les radios qu’il a lui-même bloquées. Les blocages matériels ou externes ne sont pas annulés silencieusement. Activez une radio individuellement si nécessaire.
