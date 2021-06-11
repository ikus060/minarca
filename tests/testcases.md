Minarca testcases
-----------------

This document present a list of scenarios to be tested.

### TC400 - Installation

* TC401 - Install Minarca on Windows 10 using exe
  * Check if icon is created on Desktop
  * Check if icon is created in StartMenu
* TC402 - Install Minarca on Debian using apt
* TC403 - Install Minarca on MacOS X using dmg


### TC500 - User authentication

* TC510 – Se connecter en tant que nouvel usager<br>C/A : connexion
* TC520 – Se connecter sans mot de passe <br>C/A : (\*\*\*!\*\*\* ***Veuillez renseigner ce champ***)
* TC530 – Se connecter sans nom d'usager<br>C/A : (\*\*\*!\*\*\* ***Veuillez renseigner ce champ***)
* TC540 – Se connecter avec un mauvais mot de passe<br>C/A : message d'erreur (\*\*\*Avertissement! Nom d'utilisateur ou mot de passe invalide.\*\*\*)
* TC550 – Se connecter avec un mauvais nom d'usager<br>C/A : message d'erreur (\*\*\*Avertissement! Nom d'utilisateur ou mot de passe invalide.\*\*\*)
* TC551 – Se connecter avec les bonnes informations<br>C/A : connexion

### TC1400 - Interface client

* TC1410 – Démarer une instance de minarca client. Démarer une second instance de minarca client.</p><p></p><p>**C/A:** La seconde instance de minarca client ne démarre pas.</p>
* TC1410 – Vérifier que tous les textes sont bien traduits
* TC1420 – Vérifier que les icônes sont bien affichées (icône Minarca, paramètres, informations, aide)
* TC1430 – Cliquez sur le lien vers le site web de Minarca<br>**C/A web:** Votre navigateur internet doit ouvrir une page vers la page de connexion Minarca (minarca.net ou sestican selon le cas)
* TC1440 – Connectez-vous sur l'interface web à partir du lien client<br>**C/A web:** Vous entrerez directement dans le dernier dépôt ajouté
* TC1450 – Cliquez sur le bouton "**Aide**"<br>**C/A web:** Vous serez redirigé vers la FAQ du site web de Minarca
* TC1460 – Cliquez sur le bouton "**À propos**"<br>**C/A client:** Une fenêtre "**À propos de Minarca**" s'affichera

### TC1500 - Paramètres de sauvegarde

* TC1510 – Cliquez sur le bouton de paramètres de la section "**Sauvegarde sélective**"<br>**C/A client:** Une fenêtre "**Sauvegarde sélective**" s'ouvrira
* TC1520 – Vérifier que les boutons d'activation de sauvegarde fonctionnent correctement<br>**C/A client:** Les boutons doivent basculer de "**Oui**" à "**Non**"
* TC1530 – Désactivez le répertoire: Photos , cliquez sur démarrer une sauvegarde<br>**C/A client:** Une sauvegarde démarrera
* TC1540 – Aller vérifier dans le section "**Dépôts**" de l'interface web votre nouvelle sauvegarde <br>**C/A web:** La date de révision du répertoire: Photos ne devrait pas avoir été mis à jour avec votre sauvegarde précédente.
* TC1550 – Ajoutez un nouveau dossier dans la section "**Personnaliser**" et démarrez une nouvelle sauvegarde <br>**C/A web:** Dans la section "**Fichiers**" votre dossier doit s'être ajouté
* TC1560 – Supprimer le dossier que vous avez ajouté précédemment et faites une nouvelle sauvegarde<br>**C/A web** La date de révision du dossier ne devrait pas avoir été mis à jour avec votre sauvegarde précédente.
* TC1570 –Ajoutez un nouveau fichier dans la section "**Personnaliser**" et démarrez une nouvelles sauvegarde<br>**C/A web:** Dans la section "**Fichiers**" votre fichier doit s'être ajouté
* TC1580 – Supprimer le fichier que vous avez ajouté précédemment et faites une nouvelle sauvegarde<br>**C/A web:** La date de révision du dossier ne devrait pas avoir été mis à jour avec votre sauvegarde précédente.
* TC1585 – Ajouter le disque /D et démarrer une sauvegarde<br>\*\*C/A client: Un nouveau dépôt se crééra dans l'onglet dépôt portant le même nom et se terminant par /D
* TC1586 – Supprimer le disque /D et démarrer une sauvegarde<br>\*\*C/A client: Le répertoire /D n'aura pas été mis à jour dans l'onglet dépôt.
* TC1590 – Activez le répertoire: Fichiers système et démarrez une nouvelle sauvegarde, cela prendra un certain temps<br>**C/A web:** Message (**Sauvegarde en cours**) s'affichera dans l'interface web.
* TC1595 – Pendant l'exécution de la sauvegarde, appuyez sur le bouton "**arrêter**" du client Minarca<br>**C/A client:** Message "**Interrompu**" s'affichera
\*\*\* Pour tous types de bugs veuillez vous référer à la **Procédure E**

### TC1600 - Paramètres de planification

* TC1610 – Dans la section "**Planification**" définissez la fréquence de sauvegarde à "**Heure,Quotidien,Mensuel**" <br>**C/A client:** Dans le planificateur de tâche de Windows, la tâche Minarca devrait s'exécuter à chaque heure pour vérifier la fréquence.
