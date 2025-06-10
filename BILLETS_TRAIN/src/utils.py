"""
Fonctions utilitaires pour le traitement des références de billets
"""

import sys
import subprocess
from typing import Optional
from .config import GARES_VALIDES


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