"""
Configuration et constantes pour le gestionnaire de billets de train
"""

# Gares valides reconnues par le système
GARES_VALIDES = {
    'ANGERS', 'BORDEAUX', 'CAEN', 'CHAMBERY', 'GRENOBLE',
    'LA_ROCHELLE', 'LILLE', 'LYON', 'MARSEILLE', 'NANTES',
    'PARIS', 'RENNES', 'STRASBOURG', 'TOULOUSE', 'VALENCE', 'POITIERS'
}

# Configuration par défaut
CHEMIN_CSV_DEFAUT = 'data.csv'
REPERTOIRE_PDF_DEFAUT = 'BILLETS_PDF'
REPERTOIRE_SORTIE_DEFAUT = 'OUTPUT'
REPERTOIRE_GRAPHIQUES = 'graphs'

# Fichiers de sortie
FICHIER_STATS = 'statistiques_repartition.txt'
FICHIER_REFS_NON_ATTRIBUEES = 'references_non_attribuees.csv'

# Configuration graphiques
DPI_GRAPHIQUES = 300
SEUIL_AFFICHAGE_POURCENTAGE = 0.05  # 5% 