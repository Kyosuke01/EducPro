# Rapport de Mise à Jour de la Base de Données

## Actions Réalisées

1. **Mise à jour des mots de passe existants** : Les mots de passe de tous les utilisateurs (10 étudiants et 6 enseignants existants) ont été mis à jour avec des mots de passe générés aléatoirement et hashés via `bcrypt`.
2. **Création d'utilisateurs** : Un script de peuplement (usant de `faker`) a été écrit et exécuté sur le backend pour ajouter 1 000 utilisateurs afin de tester la charge avec des données francophones cohérentes :
   - Ajout global de **950 étudiants** répartis dans les diverses classes existantes.
   - Ajout de **48 professeurs**, respectant environ un ratio d'un prof pour 20 élèves.
   - Ajout de **2 administrateurs** (profil professeur, mais avec la variable de type administrateur `is_admin = 1`).

## Comptes de Test

Voici les identifiants en environnement de test pour les différents rôles :

### 1. Compte Élève
- **Email** : `test_student@educpro.fr`
- **Mot de passe** : `*HF^BDMQPf$l`

### 2. Compte Professeur (Enseignant)
- **Email** : `test_teacher@educpro.fr`
- **Mot de passe** : `fkXSbs5V7OZw`

### 3. Compte Administrateur (Admin)
- **Email** : `test_admin@educpro.fr`
- **Mot de passe** : `sc@2WJ8unCEp`

## Note de Sécurité
Tous les nouveaux mots de passe excepté pour les profils de test ont été générés de manière robuste avec 12 caractères englobant lettres, chiffres et caractères spéciaux et n'ont été stockés qu'exclusivement sous forme de hash `bcrypt`.
