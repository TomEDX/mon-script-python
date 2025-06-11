"""
Classe principale pour la gestion des billets de train
"""

import csv
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Any

from .config import (
    CHEMIN_CSV_DEFAUT, REPERTOIRE_PDF_DEFAUT, REPERTOIRE_SORTIE_DEFAUT,
    FICHIER_STATS, FICHIER_REFS_NON_ATTRIBUEES,
    GARES_VALIDES, SEUIL_AFFICHAGE_POURCENTAGE
)
from .utils import (
    installer_si_necessaire, nettoyer_reference, extraire_gare_depart,
    extraire_gare_arrivee, est_reference_valide, formater_pourcentage
)


class GestionnaireBillets:
    """Classe principale pour gérer les billets et générer les analyses"""
    
    def __init__(self, chemin_csv: str = CHEMIN_CSV_DEFAUT, 
                 repertoire_pdf: str = REPERTOIRE_PDF_DEFAUT,
                 repertoire_sortie: str = REPERTOIRE_SORTIE_DEFAUT):
        
        self.chemin_csv = Path(chemin_csv)
        self.repertoire_pdf = Path(repertoire_pdf)
        self.repertoire_sortie = Path(repertoire_sortie)
        self.repertoire_sortie.mkdir(exist_ok=True)
        
        # Installation et import des dépendances
        installer_si_necessaire('pandas')
        installer_si_necessaire('pypdf')
        
        import pandas as pd
        from pypdf import PdfWriter, PdfReader
        
        self.pd = pd
        self.PdfWriter = PdfWriter
        self.PdfReader = PdfReader
        
        self.df = None
        self.stats_contenu = []
    
    def log_stat(self, texte: str = '') -> None:
        """Ajoute une ligne aux statistiques"""
        print(texte)
        self.stats_contenu.append(texte)
    
    def charger_donnees(self) -> None:
        """Charge les données depuis le CSV"""
        self.df = self.pd.read_csv(self.chemin_csv)
    
    def extraire_references_personne(self, row) -> List[str]:
        """Extrait les références d'une personne"""
        refs = []
        for col in ['Aller 1', 'Aller 2', 'Retour 1', 'Retour 2']:
            if col in self.df.columns:
                val = row[col]
                refs.append('--' if self.pd.isna(val) else str(val))
            else:
                refs.append('--')
        return refs
    
    def analyser_trajet(self, ref1: str, ref2: str) -> Dict[str, Any]:
        """Analyse un trajet (aller ou retour)"""
        if self.pd.isna(ref1): ref1 = '--'
        if self.pd.isna(ref2): ref2 = '--'
        ref1, ref2 = str(ref1), str(ref2)
        
        if not est_reference_valide(ref1):
            return {'gare_depart': None, 'gare_arrivee': None, 'est_direct': True}
        
        gare_depart = extraire_gare_depart(ref1)
        
        if est_reference_valide(ref2):
            # Trajet avec escale
            return {
                'gare_depart': gare_depart,
                'gare_arrivee': extraire_gare_arrivee(ref2),
                'est_direct': False
            }
        else:
            # Trajet direct
            return {
                'gare_depart': gare_depart,
                'gare_arrivee': extraire_gare_arrivee(ref1),
                'est_direct': True
            }
    
    def fusionner_pdfs_personne(self, nom: str, prenom: str, id_personne: str, refs: List[str]) -> bool:
        """Fusionne les PDFs de billets pour une personne"""
        refs_valides = [ref for ref in refs if est_reference_valide(ref)]
        if not refs_valides:
            return False
        
        chemins_pdf = [self.repertoire_pdf / f"{ref}.pdf" for ref in refs_valides]
        manquants = [ref for ref, chemin in zip(refs_valides, chemins_pdf) if not chemin.is_file()]
        
        if manquants:
            print(f"PDF manquants pour {nom} {prenom} : {', '.join(manquants)}")
            return False
        
        try:
            writer = self.PdfWriter()
            for chemin_pdf in chemins_pdf:
                try:
                    with open(chemin_pdf, "rb") as f:
                        reader = self.PdfReader(f)
                        for page in reader.pages:
                            writer.add_page(page)
                except Exception as e:
                    print(f"Erreur PDF {chemin_pdf}: {e}")
                    continue
            
            nom_fichier = f"{nom}_{prenom}_{id_personne}.pdf"
            with open(self.repertoire_sortie / nom_fichier, "wb") as f:
                writer.write(f)
            return True
            
        except Exception as e:
            print(f"Erreur fusion {nom} {prenom}: {e}")
            return False
    
    def detecter_billets_non_utilises(self) -> int:
        """Détecte les billets non attribués et sauvegarde en CSV"""
        refs_attribuees = set()
        for _, row in self.df.iterrows():
            for ref in self.extraire_references_personne(row):
                if est_reference_valide(ref):
                    refs_attribuees.add(ref)
        
        refs_non_attribuees = []
        for pdf_file in self.repertoire_pdf.glob('*.pdf'):
            ref = pdf_file.stem
            if ref not in refs_attribuees:
                ref_propre = nettoyer_reference(ref)
                if '_' in ref_propre and '-' in ref_propre:
                    gares = ref_propre.split('-')
                    if len(gares) != 2 or not all(g in GARES_VALIDES for g in gares):
                        refs_non_attribuees.append([ref, "Format invalide"])
                else:
                    refs_non_attribuees.append([ref, "Pas de référence dans le CSV"])
        
        if refs_non_attribuees:
            with open(FICHIER_REFS_NON_ATTRIBUEES, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Reference', 'Raison'])
                writer.writerows(refs_non_attribuees)
        
        return len(refs_non_attribuees)
    
    def generer_toutes_les_statistiques(self) -> None:
        """Génère toutes les statistiques"""
        self.log_stat('=== STATISTIQUES DE RÉPARTITION ===')
        
        # Statistiques des fichiers
        nb_pdf_source = len(list(self.repertoire_pdf.glob('*.pdf')))
        nb_pdf_fusionnes = len(list(self.repertoire_sortie.glob('*.pdf')))
        self.log_stat(f"\nNombre de PDF dans {self.repertoire_pdf.name} : {nb_pdf_source}")
        self.log_stat(f"Nombre de billets fusionnés dans {self.repertoire_sortie.name} : {nb_pdf_fusionnes}")
        
        # Billets non utilisés
        nb_non_utilises = self.detecter_billets_non_utilises()
        if nb_non_utilises > 0:
            self.log_stat(f"\nNombre de références non attribuées : {nb_non_utilises}")
            self.log_stat(f"Détails sauvegardés dans '{FICHIER_REFS_NON_ATTRIBUEES}'")
        
        # Analyse des trajets
        stats_trajets = {'aller_direct': 0, 'aller_escale': 0, 'retour_direct': 0, 'retour_escale': 0}
        gares_depart = []
        gares_arrivee_aller = []
        gares_arrivee_retour = []
        trajets_symetriques = []
        
        for _, row in self.df.iterrows():
            refs = self.extraire_references_personne(row)
            
            # Analyse aller et retour
            aller = self.analyser_trajet(refs[0], refs[1])
            retour = self.analyser_trajet(refs[2], refs[3])
            
            # Stats aller
            if aller['gare_depart']:
                gares_depart.append(aller['gare_depart'])
                if aller['est_direct']:
                    stats_trajets['aller_direct'] += 1
                else:
                    stats_trajets['aller_escale'] += 1
                if aller['gare_arrivee']:
                    gares_arrivee_aller.append(aller['gare_arrivee'])
            
            # Stats retour
            if retour['gare_depart']:
                if retour['est_direct']:
                    stats_trajets['retour_direct'] += 1
                else:
                    stats_trajets['retour_escale'] += 1
                if retour['gare_arrivee']:
                    gares_arrivee_retour.append(retour['gare_arrivee'])
            
            # Trajets symétriques
            if (aller['gare_depart'] and aller['gare_arrivee'] and 
                retour['gare_depart'] and retour['gare_arrivee'] and
                aller['gare_depart'] == retour['gare_arrivee'] and 
                aller['gare_arrivee'] == retour['gare_depart']):
                trajets_symetriques.append(f"{aller['gare_depart']}-{aller['gare_arrivee']}")
        
        # Affichage des statistiques
        self._afficher_statistiques_gares_depart(gares_depart)
        self._afficher_statistiques_types_billets()
        self._afficher_statistiques_trajets(stats_trajets)
        self._afficher_statistiques_gares_arrivee(gares_arrivee_aller, gares_arrivee_retour)
        self._afficher_trajets_symetriques(trajets_symetriques)
        
        # Sauvegarde
        with open(FICHIER_STATS, 'w', encoding='utf-8') as f:
            for ligne in self.stats_contenu:
                f.write(ligne + '\n')
    
    def _afficher_statistiques_gares_depart(self, gares_depart: List[str]) -> None:
        """Affiche les statistiques des gares de départ"""
        if gares_depart:
            self.log_stat('\nRépartition par gare de départ :')
            for gare, count in Counter(gares_depart).most_common():
                self.log_stat(f"  {gare} : {formater_pourcentage(count, len(gares_depart))}")
    
    def _afficher_statistiques_types_billets(self) -> None:
        """Affiche les statistiques des types de billets"""
        for col, nom in [('Type de billet 19 juin', 'Aller'), ('Type de billet 21', 'Retour')]:
            if col in self.df.columns:
                types = self.df[col].value_counts()
                self.log_stat(f'\nRépartition par type de billet ({nom}) :')
                for typ, count in types.items():
                    self.log_stat(f"  {typ} : {formater_pourcentage(count, types.sum())}")
    
    def _afficher_statistiques_trajets(self, stats_trajets: Dict[str, int]) -> None:
        """Affiche les statistiques des trajets"""
        self.log_stat('\n=== STATISTIQUES DES TRAJETS ===')
        total_aller = stats_trajets['aller_direct'] + stats_trajets['aller_escale']
        total_retour = stats_trajets['retour_direct'] + stats_trajets['retour_escale']
        
        if total_aller > 0:
            self.log_stat(f"Trajets aller directs : {formater_pourcentage(stats_trajets['aller_direct'], total_aller)}")
            self.log_stat(f"Trajets aller avec escale : {formater_pourcentage(stats_trajets['aller_escale'], total_aller)}")
        if total_retour > 0:
            self.log_stat(f"Trajets retour directs : {formater_pourcentage(stats_trajets['retour_direct'], total_retour)}")
            self.log_stat(f"Trajets retour avec escale : {formater_pourcentage(stats_trajets['retour_escale'], total_retour)}")
    
    def _afficher_statistiques_gares_arrivee(self, gares_arrivee_aller: List[str], gares_arrivee_retour: List[str]) -> None:
        """Affiche les statistiques des gares d'arrivée"""
        for gares, titre in [(gares_arrivee_aller, "aller"), (gares_arrivee_retour, "retour")]:
            if gares:
                self.log_stat(f"\nRépartition des gares d'arrivée ({titre}) :")
                for gare, count in Counter(gares).most_common():
                    if count / len(gares) > SEUIL_AFFICHAGE_POURCENTAGE:  # Seuil 5%
                        self.log_stat(f"  {gare} : {formater_pourcentage(count, len(gares))}")
    
    def _afficher_trajets_symetriques(self, trajets_symetriques: List[str]) -> None:
        """Affiche les trajets symétriques"""
        if trajets_symetriques:
            self.log_stat('\n=== TRAJETS SYMÉTRIQUES ===')
            self.log_stat('\nTrajets symétriques les plus fréquents :')
            for trajet, count in Counter(trajets_symetriques).most_common():
                if count / len(trajets_symetriques) > SEUIL_AFFICHAGE_POURCENTAGE:
                    self.log_stat(f"  {trajet} : {formater_pourcentage(count, len(trajets_symetriques))}")
    
    def executer_analyse_complete(self) -> None:
        """Exécute l'analyse complète"""
        print("Chargement des données...")
        self.charger_donnees()
        
        print("Fusion des PDFs...")
        for _, row in self.df.iterrows():
            nom = str(row.iloc[1]).upper().replace(' ', '')
            prenom = str(row.iloc[2]).upper().replace(' ', '')
            id_personne = str(row.iloc[0])
            refs = self.extraire_references_personne(row)
            self.fusionner_pdfs_personne(nom, prenom, id_personne, refs)
        
        print("Génération des statistiques...")
        self.generer_toutes_les_statistiques()
        
        print("Analyse terminée !")
        print(f"- PDFs fusionnés dans : {self.repertoire_sortie}")
        print(f"- Statistiques dans : {FICHIER_STATS}")
        print(f"- Références non attribuées dans : {FICHIER_REFS_NON_ATTRIBUEES}") 