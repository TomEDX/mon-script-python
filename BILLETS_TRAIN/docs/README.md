# Gestionnaire de Billets de Train

## 📁 Structure du projet

Le projet a été restructuré en modules organisés par répertoires selon les bonnes pratiques Python :

```
📦 BILLETS_TRAIN/
├── 🚀 fusion_billets.py          # Script principal (point d'entrée)
├── 📊 data.csv                   # Fichier de données (requis)
├── 📁 src/                       # Code source
│   ├── __init__.py              # Package principal
│   ├── config.py                # Configuration et constantes
│   ├── utils.py                 # Fonctions utilitaires
│   ├── visualisations.py        # Module de génération des graphiques
│   └── gestionnaire.py          # Classe principale GestionnaireBillets
├── 📁 docs/                      # Documentation
│   └── README.md                # Documentation détaillée
├── 📁 BILLETS_PDF/               # Répertoire des PDFs de billets (requis)
└── 📁 OUTPUT/                    # Répertoire de sortie
    ├── graphs/                  # Graphiques générés
    ├── *.pdf                    # PDFs fusionnés par personne
    ├── statistiques_repartition.txt
    └── references_non_attribuees.csv
```

## 🎯 Fonctionnalités

### Fusion de PDFs

- Fusion automatique des billets par personne
- Nommage intelligent : `NOM_PRENOM_ID.pdf`
- Gestion des erreurs et PDFs manquants

### Statistiques complètes

- Répartition par gares de départ/arrivée
- Types de billets par date
- Comparaison trajets directs vs avec escale
- Analyse des trajets symétriques
- Détection des billets non attribués

### Visualisations graphiques

- **Camemberts** : Types de billets par date
- **Graphiques en barres** : Gares de départ
- **Histogrammes** : Comparaison escales/direct
- **Top 10** : Destinations les plus populaires
- **Comparaisons** : Aller vs Retour

## 🛠 Utilisation

### Lancement simple

```bash
python fusion_billets.py
```

### Personnalisation

```python
from src.gestionnaire import GestionnaireBillets

# Configuration personnalisée
gestionnaire = GestionnaireBillets(
    chemin_csv='mes_donnees.csv',
    repertoire_pdf='MES_BILLETS',
    repertoire_sortie='MES_RESULTATS'
)
gestionnaire.executer_analyse_complete()
```

### Import du package

```python
# Utilisation comme package
from src import GestionnaireBillets

# Ou import direct
import src
gestionnaire = src.GestionnaireBillets()
```

## 📊 Sorties générées

1. **PDFs fusionnés** : Un PDF par personne dans `OUTPUT/`
2. **Statistiques texte** : `statistiques_repartition.txt`
3. **Références non attribuées** : `references_non_attribuees.csv`
4. **Graphiques** : Dans `OUTPUT/graphs/`
   - `types_billets_*.png`
   - `gares_depart.png`
   - `types_escales.png`
   - `comparaison_directs_escales.png`
   - `top_gares_arrivee.png`

## 🔧 Configuration

Toutes les constantes sont centralisées dans `src/config.py` :

- Gares valides
- Chemins par défaut
- Paramètres de visualisation
- Seuils d'affichage

## 📦 Modules

### 📁 `src/` - Package principal

#### `src/config.py`

Configuration centralisée et constantes du projet.

#### `src/utils.py`

Fonctions utilitaires réutilisables :

- Installation automatique des dépendances
- Traitement des références de billets
- Formatage des données

#### `src/visualisations.py`

Génération des graphiques avec matplotlib/seaborn :

- Backend non-interactif pour l'exécution batch
- Graphiques haute résolution (300 DPI)
- Palette de couleurs harmonieuse

#### `src/gestionnaire.py`

Classe principale avec toute la logique métier :

- Fusion des PDFs
- Calcul des statistiques
- Coordination des modules

### 📁 `docs/` - Documentation

Documentation complète du projet et guides d'utilisation.

### 🚀 `fusion_billets.py`

Point d'entrée simple et propre de l'application.

## 🎨 Avantages de la nouvelle structure

### 🗂️ **Organisation claire**

- **Séparation des responsabilités** : Code, docs, données séparés
- **Package structuré** : Import Python standard
- **Navigation intuitive** : Hiérarchie logique

### 🔧 **Maintenabilité**

- **Modules isolés** : Modifications ciblées
- **Configuration centralisée** : Un seul point de modification
- **Documentation organisée** : Docs dans leur propre espace

### 🔄 **Réutilisabilité**

- **Package importable** : `import src`
- **Modules indépendants** : Utilisation séparée possible
- **API claire** : Interfaces bien définies

### 🧪 **Testabilité**

- **Structure modulaire** : Tests par module
- **Imports relatifs** : Dépendances claires
- **Séparation code/config** : Tests isolés

### 📈 **Scalabilité**

- **Ajout de modules** : Facilité d'extension
- **Sous-packages** : Organisation hiérarchique
- **Versioning** : Gestion des versions du package

## 🚀 Développement

### Ajout de nouvelles fonctionnalités

1. Créer un nouveau module dans `src/`
2. Ajouter l'import dans `src/__init__.py`
3. Documenter dans `docs/`

### Tests (future)

```
├── tests/
│   ├── test_utils.py
│   ├── test_gestionnaire.py
│   └── test_visualisations.py
```

Cette structure respecte les conventions Python et facilite la maintenance, l'extension et la collaboration sur le projet !
