#!/usr/bin/env python3
"""
Gestionnaire de billets de train - Fusion des PDFs et génération de statistiques
"""

import os
import sys
import subprocess
from pathlib import Path
import csv
from collections import Counter, defaultdict
from typing import List, Optional, Tuple

# Configuration
GARES_VALIDES = {
    'ANGERS', 'BORDEAUX', 'CAEN', 'CHAMBERY', 'GRENOBLE',
    'LA_ROCHELLE', 'LILLE', 'LYON', 'MARSEILLE', 'NANTES',
    'PARIS', 'RENNES', 'STRASBOURG', 'TOULOUSE', 'VALENCE', 'POITIERS'
}

def installer_si_necessaire(package: str) -> None:
    """Installe un package Python s'il n'est pas présent"""
    try:
        __import__(package)
    except ImportError:
        print(f"Installation du package manquant : {package}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def nettoyer_reference(ref: str) -> str:
    """Nettoie une référence : GARE1-GARE2_INFOS -> GARE1-GARE2"""
    if not isinstance(ref, str) or ref == '--':
        return ref
    if '_' in ref:
        partie_gares = ref.split('_')[0]
        if '-' in partie_gares:
            gares = partie_gares.split('-')
            if len(gares) == 2 and all(g in GARES_VALIDES for g in gares):
                return partie_gares
    elif '-' in ref:
        gares = ref.split('-')
        if len(gares) == 2 and all(g in GARES_VALIDES for g in gares):
            return ref
    return ref

def extraire_gare_depart(ref: str) -> Optional[str]:
    """Extrait la gare de départ d'une référence"""
    if not isinstance(ref, str) or ref == '--':
        return None
    ref_propre = nettoyer_reference(ref)
    if '-' in ref_propre:
        gare = ref_propre.split('-')[0]
        return gare if gare in GARES_VALIDES else None
    return None

def extraire_gare_arrivee(ref: str) -> Optional[str]:
    """Extrait la gare d'arrivée d'une référence"""
    if not isinstance(ref, str) or ref == '--':
        return None
    ref_propre = nettoyer_reference(ref)
    if '-' in ref_propre:
        parts = ref_propre.split('-')
        if len(parts) >= 2:
            gare = parts[1]
            return gare if gare in GARES_VALIDES else None
    return None

def est_reference_valide(ref: str) -> bool:
    """Vérifie si une référence est valide"""
    return isinstance(ref, str) and ref.strip() != "--"

def formater_pourcentage(count: int, total: int) -> str:
    """Formate un nombre avec son pourcentage"""
    if total == 0:
        return f"{count} (0%)"
    return f"{count} ({count/total*100:.1f}%)"


class GestionnaireBillets:
    """Classe principale pour gérer les billets et générer les analyses"""
    
    def __init__(self, chemin_csv: str = 'data.csv', 
                 repertoire_pdf: str = 'BILLETS_PDF',
                 repertoire_sortie: str = 'OUTPUT'):
        
        self.chemin_csv = Path(chemin_csv)
        self.repertoire_pdf = Path(repertoire_pdf)
        self.repertoire_sortie = Path(repertoire_sortie)
        self.repertoire_sortie.mkdir(exist_ok=True)
        
        # Création du répertoire des graphiques
        self.repertoire_graphiques = self.repertoire_sortie / 'graphs'
        self.repertoire_graphiques.mkdir(exist_ok=True)
        
        # Installation et import des dépendances
        installer_si_necessaire('pandas')
        installer_si_necessaire('pypdf')
        installer_si_necessaire('matplotlib')
        installer_si_necessaire('seaborn')
        
        import pandas as pd
        from pypdf import PdfWriter, PdfReader
        import matplotlib
        matplotlib.use('Agg')  # Backend non-interactif
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        self.pd = pd
        self.PdfWriter = PdfWriter
        self.PdfReader = PdfReader
        self.plt = plt
        self.sns = sns
        
        self.df = None
        self.stats_contenu = []
        
        # Stockage des données statistiques pour visualisation
        self.stats_visualisation = {
            'gares_depart': [],
            'types_billets': {},
            'stats_trajets': {},
            'compteurs_escales': {},
            'gares_arrivee_aller': [],
            'gares_arrivee_retour': [],
            'trajets_symetriques': []
        }
    
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
    
    def analyser_trajet(self, ref1: str, ref2: str) -> dict:
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
                    refs_non_attribuees.append([ref, "Pas de gare trouvée"])
        
        if refs_non_attribuees:
            with open('references_non_attribuees.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Reference', 'Raison'])
                writer.writerows(refs_non_attribuees)
        
        return len(refs_non_attribuees)
    
    def generer_toutes_les_statistiques(self) -> None:
        """Génère toutes les statistiques"""
        self.log_stat('=== STATISTIQUES DE RÉPARTITION ===')
        
        # Billets non utilisés
        nb_non_utilises = self.detecter_billets_non_utilises()
        if nb_non_utilises > 0:
            self.log_stat(f"\nNombre de références non attribuées : {nb_non_utilises}")
            self.log_stat("Détails sauvegardés dans 'references_non_attribuees.csv'")
        
        # Analyse des trajets
        stats_trajets = {'aller_direct': 0, 'aller_escale': 0, 'retour_direct': 0, 'retour_escale': 0}
        gares_depart = []
        gares_arrivee_aller = []
        gares_arrivee_retour = []
        trajets_symetriques = []
        compteurs_escales = defaultdict(int)
        
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
            
            # Comparaison escales
            if aller['gare_depart'] and retour['gare_depart']:
                if not aller['est_direct'] and not retour['est_direct']:
                    compteurs_escales['Escale à l\'aller et au retour'] += 1
                elif aller['est_direct'] and retour['est_direct']:
                    compteurs_escales['Direct à l\'aller et au retour'] += 1
                elif not aller['est_direct'] and retour['est_direct']:
                    compteurs_escales['Escale à l\'aller et direct au retour'] += 1
                elif aller['est_direct'] and not retour['est_direct']:
                    compteurs_escales['Direct à l\'aller et escale au retour'] += 1
        
        # Stockage des données pour visualisation
        self.stats_visualisation['gares_depart'] = gares_depart
        self.stats_visualisation['stats_trajets'] = stats_trajets
        self.stats_visualisation['compteurs_escales'] = dict(compteurs_escales)
        self.stats_visualisation['gares_arrivee_aller'] = gares_arrivee_aller
        self.stats_visualisation['gares_arrivee_retour'] = gares_arrivee_retour
        self.stats_visualisation['trajets_symetriques'] = trajets_symetriques
        
        # Affichage des statistiques
        if gares_depart:
            self.log_stat('\nRépartition par gare de départ :')
            for gare, count in Counter(gares_depart).most_common():
                self.log_stat(f"  {gare} : {formater_pourcentage(count, len(gares_depart))}")
        
        # Types de billets
        for col, nom in [('Type de billet 19 juin', '19 juin'), ('Type de billet 21', '21')]:
            if col in self.df.columns:
                types = self.df[col].value_counts()
                self.stats_visualisation['types_billets'][nom] = types.to_dict()
                self.log_stat(f'\nRépartition par type de billet ({nom}) :')
                for typ, count in types.items():
                    self.log_stat(f"  {typ} : {formater_pourcentage(count, types.sum())}")
        
        # Statistiques trajets
        self.log_stat('\n=== STATISTIQUES DES TRAJETS ===')
        total_aller = stats_trajets['aller_direct'] + stats_trajets['aller_escale']
        total_retour = stats_trajets['retour_direct'] + stats_trajets['retour_escale']
        
        if total_aller > 0:
            self.log_stat(f"Trajets aller directs : {formater_pourcentage(stats_trajets['aller_direct'], total_aller)}")
            self.log_stat(f"Trajets aller avec escale : {formater_pourcentage(stats_trajets['aller_escale'], total_aller)}")
        if total_retour > 0:
            self.log_stat(f"Trajets retour directs : {formater_pourcentage(stats_trajets['retour_direct'], total_retour)}")
            self.log_stat(f"Trajets retour avec escale : {formater_pourcentage(stats_trajets['retour_escale'], total_retour)}")
        
        # Gares d'arrivée
        for gares, titre in [(gares_arrivee_aller, "aller"), (gares_arrivee_retour, "retour")]:
            if gares:
                self.log_stat(f"\nRépartition des gares d'arrivée ({titre}) :")
                for gare, count in Counter(gares).most_common():
                    if count / len(gares) > 0.05:  # Seuil 5%
                        self.log_stat(f"  {gare} : {formater_pourcentage(count, len(gares))}")
        
        # Comparaisons aller-retour
        self.log_stat('\n=== COMPARAISON ALLER-RETOUR ===')
        
        if trajets_symetriques:
            self.log_stat('\nTrajets symétriques les plus fréquents :')
            for trajet, count in Counter(trajets_symetriques).most_common():
                if count / len(trajets_symetriques) > 0.05:
                    self.log_stat(f"  {trajet} : {formater_pourcentage(count, len(trajets_symetriques))}")
        
        if compteurs_escales:
            self.log_stat('\nComparaison des escales aller-retour :')
            total_comp = sum(compteurs_escales.values())
            for typ, count in Counter(compteurs_escales).most_common():
                if count / total_comp > 0.05:
                    self.log_stat(f"  {typ} : {formater_pourcentage(count, total_comp)}")
        
        # Sauvegarde
        with open('statistiques_repartition.txt', 'w', encoding='utf-8') as f:
            for ligne in self.stats_contenu:
                f.write(ligne + '\n')
    
    def generer_visualisations(self) -> None:
        """Génère les visualisations graphiques des statistiques"""
        print("Génération des visualisations...")
        
        # Configuration générale des graphiques
        self.plt.style.use('default')
        self.sns.set_palette("husl")
        
        # 1. Camembert - Types de billets
        self._generer_camembert_types_billets()
        
        # 2. Bar chart - Gares de départ
        self._generer_bar_chart_gares_depart()
        
        # 3. Histogramme - Escales
        self._generer_histogramme_escales()
        
        # 4. Graphiques supplémentaires
        self._generer_graphiques_supplementaires()
        
        print(f"Visualisations sauvegardées dans : {self.repertoire_graphiques}")
    
    def _generer_camembert_types_billets(self) -> None:
        """Génère les camemberts pour les types de billets"""
        for date, types in self.stats_visualisation['types_billets'].items():
            if types:
                fig, ax = self.plt.subplots(figsize=(10, 8))
                
                labels = list(types.keys())
                sizes = list(types.values())
                
                # Couleurs et mise en forme
                colors = self.plt.cm.Set3(range(len(labels)))
                wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                                  colors=colors, startangle=90)
                
                # Amélioration de la lisibilité
                for autotext in autotexts:
                    autotext.set_color('black')
                    autotext.set_fontweight('bold')
                
                ax.set_title(f'Répartition des types de billets ({date})', 
                           fontsize=14, fontweight='bold', pad=20)
                
                self.plt.tight_layout()
                self.plt.savefig(self.repertoire_graphiques / f'types_billets_{date.replace(" ", "_")}.png', 
                               dpi=300, bbox_inches='tight')
                self.plt.close()
    
    def _generer_bar_chart_gares_depart(self) -> None:
        """Génère le bar chart des gares de départ"""
        if not self.stats_visualisation['gares_depart']:
            return
        
        gares_counter = Counter(self.stats_visualisation['gares_depart'])
        gares = list(gares_counter.keys())
        counts = list(gares_counter.values())
        
        fig, ax = self.plt.subplots(figsize=(12, 8))
        
        bars = ax.bar(gares, counts, color=self.plt.cm.viridis([x/len(gares) for x in range(len(gares))]))
        
        # Ajout des valeurs sur les barres
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{count}', ha='center', va='bottom', fontweight='bold')
        
        ax.set_title('Répartition des trajets par gare de départ', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Gares de départ', fontsize=12)
        ax.set_ylabel('Nombre de trajets', fontsize=12)
        
        # Rotation des labels si nécessaire
        self.plt.xticks(rotation=45, ha='right')
        self.plt.grid(axis='y', alpha=0.3)
        self.plt.tight_layout()
        
        self.plt.savefig(self.repertoire_graphiques / 'gares_depart.png', 
                        dpi=300, bbox_inches='tight')
        self.plt.close()
    
    def _generer_histogramme_escales(self) -> None:
        """Génère l'histogramme des types d'escales"""
        if not self.stats_visualisation['compteurs_escales']:
            return
        
        labels = list(self.stats_visualisation['compteurs_escales'].keys())
        values = list(self.stats_visualisation['compteurs_escales'].values())
        
        fig, ax = self.plt.subplots(figsize=(14, 8))
        
        bars = ax.bar(range(len(labels)), values, 
                     color=self.plt.cm.plasma([x/len(labels) for x in range(len(labels))]))
        
        # Ajout des valeurs sur les barres
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{value}', ha='center', va='bottom', fontweight='bold')
        
        ax.set_title('Répartition des types de trajets (Escales vs Direct)', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Types de trajets', fontsize=12)
        ax.set_ylabel('Nombre de passagers', fontsize=12)
        
        # Labels sur l'axe X
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right')
        
        self.plt.grid(axis='y', alpha=0.3)
        self.plt.tight_layout()
        
        self.plt.savefig(self.repertoire_graphiques / 'types_escales.png', 
                        dpi=300, bbox_inches='tight')
        self.plt.close()
    
    def _generer_graphiques_supplementaires(self) -> None:
        """Génère des graphiques supplémentaires utiles"""
        
        # Graphique des trajets directs vs avec escale
        if self.stats_visualisation['stats_trajets']:
            self._generer_comparaison_directs_escales()
        
        # Top 10 des gares d'arrivée (aller)
        if self.stats_visualisation['gares_arrivee_aller']:
            self._generer_top_gares_arrivee()
    
    def _generer_comparaison_directs_escales(self) -> None:
        """Génère un graphique comparant trajets directs vs avec escale"""
        stats = self.stats_visualisation['stats_trajets']
        
        categories = ['Aller', 'Retour']
        directs = [stats.get('aller_direct', 0), stats.get('retour_direct', 0)]
        escales = [stats.get('aller_escale', 0), stats.get('retour_escale', 0)]
        
        x = range(len(categories))
        width = 0.35
        
        fig, ax = self.plt.subplots(figsize=(10, 6))
        
        bars1 = ax.bar([i - width/2 for i in x], directs, width, label='Direct', color='skyblue')
        bars2 = ax.bar([i + width/2 for i in x], escales, width, label='Avec escale', color='lightcoral')
        
        # Ajout des valeurs
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                           f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        ax.set_title('Comparaison Trajets Directs vs Avec Escale', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Type de trajet', fontsize=12)
        ax.set_ylabel('Nombre de trajets', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        self.plt.tight_layout()
        self.plt.savefig(self.repertoire_graphiques / 'comparaison_directs_escales.png', 
                        dpi=300, bbox_inches='tight')
        self.plt.close()
    
    def _generer_top_gares_arrivee(self) -> None:
        """Génère le top 10 des gares d'arrivée"""
        if not self.stats_visualisation['gares_arrivee_aller']:
            return
        
        gares_counter = Counter(self.stats_visualisation['gares_arrivee_aller'])
        top_gares = gares_counter.most_common(10)
        
        if not top_gares:
            return
        
        gares = [gare for gare, _ in top_gares]
        counts = [count for _, count in top_gares]
        
        fig, ax = self.plt.subplots(figsize=(12, 8))
        
        bars = ax.barh(gares, counts, color=self.plt.cm.Set2(range(len(gares))))
        
        # Ajout des valeurs
        for bar, count in zip(bars, counts):
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                   f'{count}', ha='left', va='center', fontweight='bold')
        
        ax.set_title('Top 10 des gares d\'arrivée (Aller)', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Nombre de trajets', fontsize=12)
        ax.set_ylabel('Gares d\'arrivée', fontsize=12)
        
        # Inverser l'ordre pour avoir le plus fréquent en haut
        ax.invert_yaxis()
        self.plt.grid(axis='x', alpha=0.3)
        self.plt.tight_layout()
        
        self.plt.savefig(self.repertoire_graphiques / 'top_gares_arrivee.png', 
                        dpi=300, bbox_inches='tight')
        self.plt.close()
    
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
        
        print("Génération des visualisations...")
        self.generer_visualisations()
        
        print("Analyse terminée !")
        print(f"- PDFs fusionnés dans : {self.repertoire_sortie}")
        print("- Statistiques dans : statistiques_repartition.txt")
        print("- Références non attribuées dans : references_non_attribuees.csv")
        print(f"- Graphiques dans : {self.repertoire_graphiques}")


def main():
    """Point d'entrée principal"""
    gestionnaire = GestionnaireBillets()
    gestionnaire.executer_analyse_complete()


if __name__ == "__main__":
    main()