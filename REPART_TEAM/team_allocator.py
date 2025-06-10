import pandas as pd
import random
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Configuration
SEED = 42
TEAM_SIZE_8 = 60  # Nombre d'équipes de 8 personnes
TEAM_SIZE_7 = 2  # Nombre d'équipes de 7 personnes
TOTAL_TEAMS = TEAM_SIZE_8 + TEAM_SIZE_7

class TeamAllocator:
    def __init__(self, csv_path: str):
        """Initialise l'allocateur d'équipes avec le chemin du fichier CSV."""
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)
        self.pairs = self._build_invitation_pairs()
        self.divisions = self._get_divisions()
        random.seed(SEED)
        
    def _build_invitation_pairs(self) -> List[Tuple[str, str]]:
        """Construit les paires inviteur-invité."""
        pairs = []
        for _, row in self.df.iterrows():
            if pd.notna(row['GuestId']):
                pairs.append((row['Id'], row['GuestId']))
        return pairs
    
    def _get_divisions(self) -> Set[str]:
        """Récupère l'ensemble unique des divisions."""
        return set(self.df['Division'].dropna().unique())
    
    def _initialize_teams(self) -> List[List[str]]:
        """Initialise les équipes vides."""
        return [[] for _ in range(TOTAL_TEAMS)]
    
    def _get_team_name(self, index: int) -> str:
        """Retourne le nom de l'équipe formaté (ex: Team_01, Team_02, etc.)."""
        return f"Team_{index+1:02d}"
    
    def _get_team_size_limit(self, team_index: int) -> int:
        """Retourne la taille limite pour une équipe donnée."""
        return 8 if team_index < TEAM_SIZE_8 else 7
    
    def _calculate_team_diversity_score(self, team: List[str], candidate_id: str) -> float:
        """Calcule un score de diversité pour une équipe avec un candidat potentiel."""
        if not team:  # Si l'équipe est vide, retourner un score neutre
            return 0.0
            
        # Récupérer les informations du candidat
        candidate_info = self.df[self.df['Id'] == candidate_id].iloc[0]
        candidate_division = candidate_info['Division']
        candidate_is_compagnon = candidate_info['IsCompagnons'] == 'OUI'
        candidate_has_guest = pd.notna(candidate_info['GuestId'])
        
        # Récupérer les informations actuelles de l'équipe
        team_info = self.df[self.df['Id'].isin(team)]
        
        # 1. Score basé sur la diversité des divisions
        division_score = 0.0
        if pd.notna(candidate_division):
            existing_divisions = set(team_info['Division'].dropna())
            if candidate_division not in existing_divisions:
                division_score += 1.0
                
        # 2. Score basé sur la mixité compagnons/non-compagnons
        compagnon_score = 0.0
        team_compagnons = (team_info['IsCompagnons'] == 'OUI').sum()
        if candidate_is_compagnon and team_compagnons < len(team) / 2:
            compagnon_score += 1.0
        elif not candidate_is_compagnon and team_compagnons > len(team) / 2:
            compagnon_score += 1.0

        # 3. Score basé sur la répartition des paires inviteur-invité
        pair_score = 0.0
        team_pairs = sum(1 for _, row in team_info.iterrows() if pd.notna(row['GuestId']))
        
        # Pénaliser les équipes qui ont déjà beaucoup de paires
        if candidate_has_guest:
            if team_pairs == 0:
                pair_score += 2.0  # Bonus important pour une équipe sans paire
            elif team_pairs == 1:
                pair_score += 1.0  # Petit bonus pour une équipe avec une seule paire
            else:
                pair_score -= team_pairs * 0.5  # Pénalité croissante avec le nombre de paires
            
        return division_score + compagnon_score + pair_score
    
    def _calculate_team_stats(self) -> pd.DataFrame:
        """Calcule les statistiques par équipe."""
        stats = []
        total_pairs = len(self.pairs)
        min_pairs_per_team = total_pairs // TOTAL_TEAMS
        
        for team_idx in range(TOTAL_TEAMS):
            team_name = self._get_team_name(team_idx)
            team_members = self.df[self.df['Team'] == team_name]
            
            # Statistiques de base
            total_members = len(team_members)
            compagnons = len(team_members[team_members['IsCompagnons'] == 'OUI'])
            
            # Statistiques des divisions
            divisions = team_members['Division'].dropna().unique()
            division_count = len(divisions)
            division_list = ', '.join(sorted(divisions)) if len(divisions) > 0 else 'Aucune'
            
            # Nombre de paires inviteur-invité
            pairs = sum(1 for _, row in team_members.iterrows() if pd.notna(row['GuestId']))
            
            # Écart par rapport à la moyenne des paires
            pairs_deviation = pairs - min_pairs_per_team
            
            stats.append({
                'Équipe': team_name,
                'Nombre de membres': total_members,
                'Nombre de compagnons': compagnons,
                'Nombre de divisions': division_count,
                'Divisions': division_list,
                'Nombre de paires inviteur-invité': pairs,
                'Écart moyen paires': pairs_deviation
            })
            
        return pd.DataFrame(stats)
    
    def _validate_team_sizes(self) -> bool:
        """Vérifie que les tailles des équipes sont correctes."""
        team_sizes = self.df['Team'].value_counts()
        
        # Vérifier le nombre d'équipes
        if len(team_sizes) != TOTAL_TEAMS:
            print(f"Erreur : {len(team_sizes)} équipes créées au lieu de {TOTAL_TEAMS}")
            return False
            
        # Vérifier les tailles des équipes
        for team_name, size in team_sizes.items():
            team_num = int(team_name.split('_')[1])
            expected_size = 8 if team_num <= TEAM_SIZE_8 else 7
            if size != expected_size:
                print(f"Erreur : L'équipe {team_name} a {size} membres au lieu de {expected_size}")
                return False
                
        return True
        
    def _validate_pairs(self) -> bool:
        """Vérifie que les paires inviteur-invité sont dans la même équipe."""
        for inviter, guest in self.pairs:
            inviter_team = self.df[self.df['Id'] == inviter]['Team'].iloc[0]
            guest_team = self.df[self.df['Id'] == guest]['Team'].iloc[0]
            if inviter_team != guest_team:
                print(f"Erreur : La paire {inviter}-{guest} n'est pas dans la même équipe")
                return False
        return True
        
    def validate_allocation(self) -> bool:
        """Valide l'allocation des équipes."""
        # Vérifier que toutes les personnes sont assignées
        if self.df['Team'].isna().any():
            print("Erreur : Certaines personnes n'ont pas été assignées à une équipe")
            return False
            
        # Vérifier les tailles des équipes
        if not self._validate_team_sizes():
            return False
            
        # Vérifier les paires inviteur-invité
        if not self._validate_pairs():
            return False
            
        print("Validation réussie !")
        return True

    def allocate_teams(self) -> pd.DataFrame:
        """Alloue les personnes aux équipes en respectant les contraintes."""
        teams = self._initialize_teams()
        unassigned = set(self.df['Id'].values)
        
        # Compter le nombre total de paires
        total_pairs = len(self.pairs)
        min_pairs_per_team = total_pairs // TOTAL_TEAMS  # Nombre minimum de paires par équipe
        remaining_pairs = total_pairs % TOTAL_TEAMS      # Paires restantes à distribuer
        
        # Créer une liste des équipes avec leur quota de paires
        team_pair_quotas = [min_pairs_per_team + (1 if i < remaining_pairs else 0) 
                          for i in range(TOTAL_TEAMS)]
        
        # Trier les paires par division pour maximiser la diversité
        sorted_pairs = []
        for inviter, guest in self.pairs:
            inviter_info = self.df[self.df['Id'] == inviter].iloc[0]
            guest_info = self.df[self.df['Id'] == guest].iloc[0]
            
            # Calculer le score de diversité de la paire
            division_score = 0
            if pd.notna(inviter_info['Division']):
                division_score += 1
            if pd.notna(guest_info['Division']):
                division_score += 1
            
            compagnon_score = 0
            if inviter_info['IsCompagnons'] == 'OUI':
                compagnon_score += 1
            if guest_info['IsCompagnons'] == 'OUI':
                compagnon_score += 1
                
            sorted_pairs.append((inviter, guest, division_score, compagnon_score))
        
        # Trier les paires par leur potentiel de diversité
        sorted_pairs.sort(key=lambda x: (-x[2], -x[3]))  # Trier par division puis compagnon, ordre décroissant
        
        # Traiter d'abord les paires inviteur-invité
        for inviter, guest, _, _ in sorted_pairs:
            if inviter in unassigned:
                # Trouver la meilleure équipe pour la paire
                best_team_idx = -1
                best_score = float('-inf')
                
                for team_idx, team in enumerate(teams):
                    if len(team) + 2 <= self._get_team_size_limit(team_idx):
                        # Calculer le score de base
                        score = self._calculate_team_diversity_score(team, inviter)
                        score += self._calculate_team_diversity_score(team + [inviter], guest)
                        
                        # Facteur de quota : favoriser les équipes qui n'ont pas atteint leur quota
                        current_pairs = sum(1 for t_id in team if pd.notna(self.df[self.df['Id'] == t_id]['GuestId'].iloc[0]))
                        if current_pairs < team_pair_quotas[team_idx]:
                            score += 3.0  # Bonus important pour respecter les quotas
                        
                        # Facteur d'équilibrage : éviter les équipes qui ont déjà beaucoup de paires
                        if current_pairs > team_pair_quotas[team_idx]:
                            score -= 2.0 * (current_pairs - team_pair_quotas[team_idx])
                        
                        if score > best_score:
                            best_score = score
                            best_team_idx = team_idx
                
                if best_team_idx != -1:
                    teams[best_team_idx].extend([inviter, guest])
                    unassigned.remove(inviter)
                    unassigned.remove(guest)
        
        # Assigner le reste des personnes
        remaining = list(unassigned)
        random.shuffle(remaining)
        
        for person_id in remaining:
            best_team_idx = -1
            best_score = float('-inf')
            
            for team_idx, team in enumerate(teams):
                if len(team) < self._get_team_size_limit(team_idx):
                    score = self._calculate_team_diversity_score(team, person_id)
                    
                    # Bonus pour équilibrer les tailles d'équipes
                    score += 1.0 / (len(team) + 1)
                    
                    if score > best_score:
                        best_score = score
                        best_team_idx = team_idx
            
            teams[best_team_idx].append(person_id)
        
        # Mettre à jour le DataFrame avec les assignations
        team_assignments = {}
        for team_idx, team in enumerate(teams):
            team_name = self._get_team_name(team_idx)
            for person_id in team:
                team_assignments[person_id] = team_name
                
        self.df['Team'] = self.df['Id'].map(team_assignments)
        return self.df

    def save_results(self, output_path: str = None, stats_path: str = None):
        """Sauvegarde les résultats et les statistiques dans des fichiers CSV."""
        if output_path is None:
            output_path = 'teams_output.csv'
        if stats_path is None:
            stats_path = 'teams_stats.csv'
            
        # Sauvegarder les assignations d'équipes
        self.df.to_csv(output_path, index=False)
        print(f"Résultats sauvegardés dans {output_path}")
        
        # Calculer et sauvegarder les statistiques
        stats_df = self._calculate_team_stats()
        stats_df.to_csv(stats_path, index=False)
        print(f"Statistiques sauvegardées dans {stats_path}")

if __name__ == "__main__":
    allocator = TeamAllocator("compagnons.csv")
    allocator.allocate_teams()
    if allocator.validate_allocation():
        allocator.save_results()