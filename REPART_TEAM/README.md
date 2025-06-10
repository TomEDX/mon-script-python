# Allocateur d'Équipes pour Événement

Ce script Python permet d'allouer automatiquement 514 personnes en équipes pour un événement, en respectant des contraintes spécifiques de taille d'équipe et de diversité.

## Prérequis

- Python 3.9 ou supérieur
- pandas

Installation des dépendances :

```bash
pip install pandas
```

## Structure du CSV d'entrée

Le fichier CSV d'entrée doit contenir les colonnes suivantes :

- `Id` : identifiant unique de la personne
- `Division` : division/département (peut être vide pour les invités)
- `IsCompagnons` : "OUI" ou "NON"
- `GuestId` : ID de la personne invitée (peut être vide)
- `Team` : laissé vide, sera rempli par le script

## Utilisation

1. Placez votre fichier CSV d'entrée dans le même répertoire que le script
2. Exécutez le script :

```bash
python team_allocator.py
```

## Fichiers de sortie

Le script génère deux fichiers :

1. `teams_output.csv` : Le CSV original avec la colonne Team remplie (format : Team_01, Team_02, etc.)
2. `teams_stats.csv` : Statistiques par équipe incluant :
   - Nombre de membres
   - Nombre de compagnons
   - Nombre de divisions représentées
   - Liste des divisions
   - Nombre de paires inviteur-invité

## Format des équipes

Les équipes sont nommées avec un format numérique à deux chiffres :

- Team_01, Team_02, ..., Team_09, Team_10, etc.
- 59 équipes de 8 personnes (Team_01 à Team_59)
- 6 équipes de 7 personnes (Team_60 à Team_65)

Ce format facilite le tri et l'organisation des équipes.

## Contraintes respectées

1. Contraintes dures :

   - 59 équipes de 8 personnes
   - 6 équipes de 7 personnes
   - Les paires inviteur-invité restent ensemble
   - Chaque personne est assignée à exactement une équipe

2. Contraintes souples (optimisées) :
   - Diversité des divisions au sein des équipes
   - Équilibre entre compagnons et non-compagnons

## Validation

Le script effectue automatiquement les validations suivantes :

- Vérification des tailles d'équipes
- Vérification des paires inviteur-invité
- Calcul des statistiques de diversité par équipe

## Sortie

Le script génère :

1. Un fichier CSV avec les équipes assignées
2. Des statistiques de diversité pour chaque équipe
3. Un rapport de validation

## Note sur la reproductibilité

Le script utilise une graine aléatoire fixe (SEED = 42) pour assurer la reproductibilité des résultats.
