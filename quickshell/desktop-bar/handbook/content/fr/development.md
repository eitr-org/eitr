# Outils de développement

Principal > Développement regroupe **IA**, **Cloud**, **Comptes Git**, **Supervision**, **LazyVim** et **VS Code**. Les sélecteurs de projets ouvrent le dossier choisi dans l’éditeur ; l’intégration des thèmes actualise les éditeurs compatibles ouverts, y compris les sessions LazyVim.

**Comptes Git** configure une identité GitHub/GitLab par défaut, des règles par dossier, des clés SSH et des connexions distinctes aux CLI des fournisseurs. Chaque changement de règle exige la confirmation d’un aperçu ; il ne réécrit jamais les dépôts distants des projets ni les comptes CLI globaux. Voir [Comptes Git](handbook:git-accounts).

## Outils facultatifs

Installer > Langages de développement et Outils JavaScript installe les outils choisis. Java, Flutter et les clients de bases de données ne sont pas nécessaires à la barre, au lanceur ou aux thèmes EITR. Installer > Bases de données propose des outils facultatifs. Installer > Applications de développement propose Bruno, GitHub Desktop, Insomnia, JetBrains Toolbox, Meld, Postman, VS Code et Zed ; Installer > Productivité propose 1Password, Bitwarden, Discord, LibreOffice, Obsidian, Slack et Thunderbird. Les paquets AUR sont téléchargés et compilés sur votre ordinateur ; certaines licences interdisent leur distribution par EITR.

## Applications web

Installer > Applications web > Créer une application web demande un nom et une adresse, puis ajoute un lanceur ouvrant le site dans sa propre fenêtre. L’icône est téléchargée à la création, uniquement par HTTP(S). Un manifeste incorrect ou une icône indisponible entraîne l’utilisation de l’icône de page ou d’une icône générique de navigateur. N’incluez pas d’identifiants dans l’adresse. Lanceurs et icônes utilisent votre répertoire de données XDG, y compris un `XDG_DATA_HOME` personnalisé ; les deux menus de suppression utilisent ce même emplacement.

Les applications web nécessitent Chrome ou Chromium (Installer > Navigateurs) ; les services de streaming avec DRM, comme Netflix, nécessitent Chrome. Supprimez une application avec Delete dans Installer > Applications web ou dans le menu Applications.

## Assistants IA

Développement > IA propose Assistant par défaut et un menu pour chaque assistant installé : Claude Code, Codex, Gemini CLI, Grok Build et GitHub Copilot CLI. Installez-les depuis Installer > CLI d’IA ; en leur absence, Développement > IA y renvoie.

Démarrer une session ou ouvrir un projet LazyVim ou VS Code demande d’abord un dossier sous `~/Development` : entrez dans les dossiers pour descendre, utilisez Ouvrir pour choisir le dossier courant et Retour pour remonter ou revenir au menu depuis le niveau supérieur.

Vous pouvez aussi lancer Claude Code, Codex, Gemini CLI, Grok Build et GitHub Copilot CLI (`copilot`) par commande. Si l’outil manque, Eitr présente son rôle et propose la même installation que Installer > CLI IA. Saisissez `yes` pour installer ; Entrée annule. Sans terminal interactif, la commande se termine avec des instructions d’installation. Les exécutables installés ont priorité sur ces lanceurs. Connectez-vous depuis chaque outil ; Eitr ne fournit ni exécutables d’assistants ni identifiants.

Développement > IA > Assistant par défaut sélectionne un assistant installé sur cet ordinateur. **SUPER + Alt + A** l’ouvre dans un terminal ; sans choix par défaut, le sélecteur s’ouvre. Eitr conserve les demandes d’autorisation normales de chaque assistant.

Lors d’un changement de thème, Eitr modifie uniquement le réglage clair/sombre dans les fichiers existants et lisibles de Claude Code, Gemini CLI et Grok Build. Les autres réglages et la mise en forme sont conservés. Les clients non installés et les fichiers absents ou invalides sont ignorés ; les assistants sans réglage clair/sombre pris en charge utilisent les couleurs du terminal.

Les versions de SDK et les sources d’installation sont maintenues dans les manifestes de la distribution. Fiez-vous au sélecteur actuel : un exemple du manuel ne promet pas la dernière version du projet d’origine. L’installation peut nécessiter des téléchargements.

## Supervision

Développement > Supervision rend vos tableaux de bord accessibles par recherche. **Ajouter un tableau de bord** demande le service (Grafana, Datadog, Sentry, New Relic, Prometheus ou Autre), un nom et son adresse. Le menu l’ouvre ensuite dans le navigateur. Les entrées sont conservées uniquement sur cet ordinateur, dans `~/.config/eitr/monitoring.json` ; Delete en supprime une. N’incluez jamais de mots de passe ni de jetons dans une adresse.

**Outils de supervision** installe des outils en ligne de commande : `promtool` de Prometheus et la Sentry CLI. Les espaces de travail Amazon Managed Grafana se trouvent dans Cloud > AWS > votre compte > Grafana, avec les autres outils AWS.

## Comptes et opérations cloud

L’affichage de l’utilisation IA nécessite un client installé et configuré ; connectez-vous selon sa procédure normale. Les quotas et la facturation d’entreprise ou d’API peuvent différer des panneaux compatibles pour comptes personnels. EITR ne contient aucun identifiant de connexion.

Les menus cloud utilisent vos comptes et profils locaux. Les profils AWS proviennent de la configuration AWS locale ou de l’association de profils EITR. Google Cloud affiche des configurations gcloud nommées avec compte et projet. Sans projet, il vous en demande un à l’ouverture des outils de ressources ; Connexion reste accessible avant la découverte des projets. Azure liste les abonnements activés et leurs identifiants de locataire. Choisissez un contexte avant un outil : les outils Google Cloud et Azure se recherchent dans leur menu de contexte, pas globalement.

Ouvrir un contexte Google supprime les substitutions de projet héritées sans rapport ; les configurations sans projet en demandent un pour les outils de ressources. Le retour du terminal conserve le contexte et le projet choisi pour une configuration sans projet, sans changer les paramètres CLI globaux. Connexion, Vérifier l’authentification et Actualiser figurent dans chaque contexte détecté. La connexion Google vise le compte configuré ; la connexion Azure vise son locataire et restaure ensuite l’abonnement par défaut précédent. Actualiser dans Azure renouvelle le cache d’abonnements et affiche celui sélectionné.

Chaque menu commence par **Ajouter un compte AWS**, **Ajouter un compte GCP** ou **Ajouter un compte Azure**, pour configurer autant de comptes que nécessaire, par exemple Développement et Production d’une entreprise. Après le nom, la configuration propre à la CLI du fournisseur s’exécute : profil AWS via AWS SSO (IAM Identity Center) ou clés d’accès, configuration gcloud distincte avec connexion et projet, ou connexion Azure dont vous nommez les abonnements. Si `gcloud` ou `az` manque, son installation est proposée d’abord. **Ctrl+R** renomme un compte.

Les noms sont dans `~/.config/eitr/cloud-contexts.json`, associés au profil AWS, à la configuration gcloud ou à l’identifiant d’abonnement. EITR ne déduit pas les environnements et n’y stocke aucun identifiant secret ; Ajouter ne change jamais un compte CLI global par défaut. Grafana et les opérations cloud nécessitent les comptes et permissions correspondants. Certaines actions consultent seulement des données ; d’autres modifient des ressources distantes : vérifiez l’opération et le compte avant de confirmer.

Gardez jetons, secrets `.env` et identifiants hors des dotfiles partagés et captures d’écran. La configuration du shell charge les gestionnaires compatibles sans que les installateurs réécrivent vos profils. Apprendre conserve des références dédiées à LazyVim, tmux et cmux.

## Les assistants travaillent ensemble

Développement > IA > Permettre aux assistants de travailler ensemble est
désactivé par défaut. Activez cette option pour relier les programmes Claude,
Codex, Copilot et Grok installés qui semblent connectés à leur compte. La confirmation
nomme les assistants et explique que chaque transfert utilise l’abonnement
de l’assistant sollicité et compte dans ses limites. Les connexions uniquement
par clé API ou trousseau ne sont pas détectées. Gemini n’est pas proposé : Google
ne sert plus Gemini CLI pour les comptes personnels.

Demandez à votre assistant de consulter l’autre pour une relecture, une
explication ou une suggestion. Approuvez chaque transfert dans la demande
normale de l’assistant appelant ; Eitr n’autorise jamais ces outils à l’avance.
N’activez pas l’approbation automatique des outils du serveur assistants. Les
auxiliaires ne font que lire ; les modifications restent à votre assistant
principal. Un auxiliaire ne peut pas en appeler un autre. Une notification
indique qui a consulté qui, et chaque demande est limitée à trois minutes.
L’auxiliaire lit le répertoire de travail courant de l’appelant ; la question
et le contexte peuvent être envoyés au fournisseur de cet assistant.

L’option enregistre un serveur MCP `assistants` avec la commande de chaque
assistant (`claude mcp add`, `codex mcp add`, `copilot mcp add` et `grok mcp add`) :
chaque assistant écrit lui-même ses réglages. Un serveur existant du même nom reste intact et est
signalé. Les changements sont enregistrés seulement
sur cet ordinateur dans `~/.local/state/eitr/assistants.json` (ou `XDG_STATE_HOME`).
Désactiver l’option retire exactement les entrées d’Eitr ; si une entrée a été
modifiée ensuite, Eitr la conserve et signale le conflit. Redémarrez les sessions
d’assistants après un changement. La vérification de bout en bout avec des
comptes réels reste à effectuer séparément.

Antigravity CLI (`agy`) est disponible pour les comptes Google personnels dans Installer > CLI d’IA et via le lanceur de premier usage. Il n’est jamais inclus dans la distribution. Il s’installe avec l’installateur officiel de Google, qui vérifie le téléchargement, et vous vous connectez avec votre compte Google. Il n’est pas encore proposé comme assistant sollicité. Un `agy` déjà installé peut être lancé normalement. Gemini CLI nécessite une clé API Gemini ou un compte Google Cloud/entreprise. Antigravity n’est pas un auxiliaire de collaboration ; les tests en lecture seule et MCP avec un compte réel restent à effectuer.
