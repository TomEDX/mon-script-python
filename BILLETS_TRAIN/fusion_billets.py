#!/usr/bin/env python3
"""
Gestionnaire de billets de train - Fusion des PDFs et génération de statistiques
Script principal - Point d'entrée de l'application
"""

from src.gestionnaire import GestionnaireBillets


def main():
    """Point d'entrée principal"""
    gestionnaire = GestionnaireBillets()
    gestionnaire.executer_analyse_complete()


if __name__ == "__main__":
    main()