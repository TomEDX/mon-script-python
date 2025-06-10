"""
Module de génération des visualisations graphiques pour les statistiques de billets
"""

from pathlib import Path
from collections import Counter
from typing import Dict, List, Any
from .utils import installer_si_necessaire
from .config import DPI_GRAPHIQUES


class GenerateurVisualisations:
    """Classe responsable de la génération des graphiques statistiques"""
    
    def __init__(self, repertoire_graphiques: Path):
        # Installation et import des dépendances
        installer_si_necessaire('matplotlib')
        installer_si_necessaire('seaborn')
        
        import matplotlib
        matplotlib.use('Agg')  # Backend non-interactif
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        self.plt = plt
        self.sns = sns
        self.repertoire_graphiques = repertoire_graphiques
        
        # Configuration générale des graphiques
        self.plt.style.use('default')
        self.sns.set_palette("husl")
    
    def generer_toutes_visualisations(self, stats_data: Dict[str, Any]) -> None:
        """Génère toutes les visualisations à partir des données statistiques"""
        print("Génération des visualisations...")
        
        # 1. Camembert - Types de billets
        self._generer_camembert_types_billets(stats_data.get('types_billets', {}))
        
        # 2. Bar chart - Gares de départ
        self._generer_bar_chart_gares_depart(stats_data.get('gares_depart', []))
        
        # 3. Histogramme - Escales
        self._generer_histogramme_escales(stats_data.get('compteurs_escales', {}))
        
        # 4. Graphiques supplémentaires
        self._generer_graphiques_supplementaires(stats_data)
        
        print(f"Visualisations sauvegardées dans : {self.repertoire_graphiques}")
    
    def _generer_camembert_types_billets(self, types_billets: Dict[str, Dict]) -> None:
        """Génère les camemberts pour les types de billets"""
        for date, types in types_billets.items():
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
                               dpi=DPI_GRAPHIQUES, bbox_inches='tight')
                self.plt.close()
    
    def _generer_bar_chart_gares_depart(self, gares_depart: List[str]) -> None:
        """Génère le bar chart des gares de départ"""
        if not gares_depart:
            return
        
        gares_counter = Counter(gares_depart)
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
                        dpi=DPI_GRAPHIQUES, bbox_inches='tight')
        self.plt.close()
    
    def _generer_histogramme_escales(self, compteurs_escales: Dict[str, int]) -> None:
        """Génère l'histogramme des types d'escales"""
        if not compteurs_escales:
            return
        
        labels = list(compteurs_escales.keys())
        values = list(compteurs_escales.values())
        
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
                        dpi=DPI_GRAPHIQUES, bbox_inches='tight')
        self.plt.close()
    
    def _generer_graphiques_supplementaires(self, stats_data: Dict[str, Any]) -> None:
        """Génère des graphiques supplémentaires utiles"""
        
        # Graphique des trajets directs vs avec escale
        if stats_data.get('stats_trajets'):
            self._generer_comparaison_directs_escales(stats_data['stats_trajets'])
        
        # Top 10 des gares d'arrivée (aller)
        if stats_data.get('gares_arrivee_aller'):
            self._generer_top_gares_arrivee(stats_data['gares_arrivee_aller'])
    
    def _generer_comparaison_directs_escales(self, stats_trajets: Dict[str, int]) -> None:
        """Génère un graphique comparant trajets directs vs avec escale"""
        categories = ['Aller', 'Retour']
        directs = [stats_trajets.get('aller_direct', 0), stats_trajets.get('retour_direct', 0)]
        escales = [stats_trajets.get('aller_escale', 0), stats_trajets.get('retour_escale', 0)]
        
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
                        dpi=DPI_GRAPHIQUES, bbox_inches='tight')
        self.plt.close()
    
    def _generer_top_gares_arrivee(self, gares_arrivee: List[str]) -> None:
        """Génère le top 10 des gares d'arrivée"""
        if not gares_arrivee:
            return
        
        gares_counter = Counter(gares_arrivee)
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
                        dpi=DPI_GRAPHIQUES, bbox_inches='tight')
        self.plt.close() 