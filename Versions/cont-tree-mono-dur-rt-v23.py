#!/usr/bin/python
# -*- coding: latin-1 -*-

import time
import random

class PrefixTreeNode:
    """
    Représente un n½ud dans un arbre préfixé monophonique linéaire.
    Chaque n½ud ne possède qu'un seul enfant (car l'arbre est linéaire)
    et une unique continuation (la note associée à toute la branche).
    """
    def __init__(self):
        self.child = None
        self.continuation = None

class PrefixTreeContinuator:
    """
    Continuateur monophonique basé sur la méthode de François Pachet.
    
    Pour une séquence [A, B, C, D], il crée exactement 3 arbres distincts :
      - k = 1 : Préfixe [A] ? branche = [A] avec continuation = B.
      - k = 2 : Préfixe [A, B] ? branche = [B, A] avec continuation = C.
      - k = 3 : Préfixe [A, B, C] ? branche = [C, B, A] avec continuation = D.
    """
    def __init__(self, silence_threshold=2.0):
        self.roots = {}   # Dictionnaire : clé = racine (premier élément du préfixe inversé), valeur = l'arbre
        self.sequences = []  # Liste des séquences (listes de notes)
        self.silence_threshold = silence_threshold

    def train(self, sequence):
        """
        Entraîne l'arbre avec une séquence donnée.
        On considère uniquement la hauteur des notes.
        Pour chaque k de 1 à len(sequence)-1, on construit un arbre linéaire
        en inversant le préfixe [s?,..., s???] et on associe la continuation s?.
        """
        notes = [note for note, dur in sequence]
        self.sequences.append(notes)

        # Pour k variant de 1 à len(notes)-1
        for k in range(1, len(notes)):
            prefix = notes[:k]         # Sous-séquence [s?, ..., s???]
            cont = notes[k]            # La continuation est la note s?
            rev_prefix = prefix[::-1]  # Inversion du préfixe : [s???, ..., s?]
            root_note = rev_prefix[0]  # La racine de cet arbre est s???

            # Si cet arbre n'existe pas encore, le créer
            if root_note not in self.roots:
                self.roots[root_note] = PrefixTreeNode()
            node = self.roots[root_note]

            # Parcourir rev_prefix (à partir du 2ème élément)
            for note in rev_prefix[1:]:
                if node.child is None:
                    node.child = PrefixTreeNode()
                node = node.child

            # Définir la continuation unique pour toute cette branche
            if node.continuation is None:
                node.continuation = cont

    def display_memory(self):
        """Affiche l'ensemble des arbres préfixés construits."""
        print("\n?? **Arbres préfixés - Mémoire des séquences enregistrées**")
        # Pour chaque arbre, on affiche la branche complète avec la continuation
        for root_note, root in self.roots.items():
            print(f"\n?? Racine : {root_note}")
            self.display_tree(root, [root_note], level=1)

    def display_tree(self, node, branch, level):
        indent = "    " * level
        # Affichage de la branche actuelle avec la continuation
        if node.continuation is not None:
            print(f"{indent}{' -> '.join(map(str, branch))} [ {node.continuation} ]")
        else:
            print(f"{indent}{' -> '.join(map(str, branch))}")
        if node.child is not None:
            self.display_tree(node.child, branch + [node.child.continuation if node.child.continuation is not None else "?"], level+1)

    def generate(self, seed, length=10):
        """
        Génère une continuation en se basant sur la séquence d'entrée (seed).
        Pour la génération, on utilise le seed complet comme base, et on choisit l'arbre
        correspondant à la sous-séquence la plus longue.
        Ici, pour simplifier, nous ne fusionnons pas les arbres existants ; 
        on se contente de parcourir l'arbre dont la racine correspond à la dernière note du seed.
        """
        if not self.sequences:
            print("?? Aucun apprentissage disponible, génération impossible.")
            return []

        # Utiliser le seed complet (liste de tuples) pour extraire les notes
        generated = [note for note, dur in seed]
        # Pour la génération, on choisit l'arbre dont la racine est la dernière note du seed inversé.
        # Or, selon notre construction, le seed doit être la séquence entière.
        # Par simplicité, nous utilisons la dernière note du seed comme critère.
        root_note = generated[-1]
        if root_note not in self.roots:
            print("?? Aucun arbre correspondant trouvé, génération impossible.")
            return []
        node = self.roots[root_note]
        branch = [root_note]
        for _ in range(length):
            if node.child is not None and node.child.continuation is not None:
                next_note = node.child.continuation
                branch.append(next_note)
                node = node.child
            else:
                print("?? Fin de la branche, génération terminée.")
                break
        generated.extend(branch[1:])  # Ajouter la branche (hors la première note déjà présente)
        print("\n?? **Continuation générée**:")
        print("??", " -> ".join(map(str, generated)))
        return generated

    def play_output(self, notes):
        """Simule la lecture MIDI en affichant la séquence générée."""
        print("\n[PLAY OUTPUT]")
        print("Notes jouées :", " -> ".join(map(str, notes)))

# ------------------- Mode Test -------------------
if __name__ == '__main__':
    continuator = PrefixTreeContinuator(silence_threshold=2.0)

    # Séquence 1 : [48, 50, 52, 53] (Do, Ré, Mi, Fa)
    sequence1 = [(48, 0.5), (50, 0.5), (52, 0.5), (53, 0.5)]
    print("=== Entraînement avec la séquence 1 : Do, Ré, Mi, Fa (48, 50, 52, 53) ===")
    continuator.train(sequence1)
    continuator.display_memory()

    print("\n=== Génération pour la séquence 1 ===")
    continuation1 = continuator.generate(sequence1, length=10)
    print("Continuation générée :", continuation1)

    # Simuler un silence (ici, on n'attend pas vraiment, on passe à la séquence 2)
    time.sleep(2)

    # Séquence 2 : [48, 50, 50, 52] (Do, Ré, Ré, Mi)
    sequence2 = [(48, 0.5), (50, 0.5), (50, 0.5), (52, 0.5)]
    print("\n=== Entraînement avec la séquence 2 : Do, Ré, Ré, Mi (48, 50, 50, 52) ===")
    continuator.train(sequence2)
    continuator.display_memory()

    print("\n=== Génération pour la séquence 2 ===")
    continuation2 = continuator.generate(sequence2, length=10)
    print("Continuation générée :", continuation2)
