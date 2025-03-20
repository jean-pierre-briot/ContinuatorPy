#!/usr/bin/python
# -*- coding: latin-1 -*-

import time
import random

class PrefixTreeNode:
    """Représente un n½ud dans un arbre préfixé monophonique linéaire."""
    def __init__(self):
        self.child = None         # Un seul fils (structure linéaire)
        self.continuation = None   # La continuation unique associée à cette branche

class PrefixTreeContinuator:
    """
    Continuateur monophonique basé sur la méthode de François Pachet.
    
    Pour une séquence [A, B, C, D] (ex. [48, 50, 52, 53]), il crée :
      - Arbre 1 : [48] avec continuation 50.
      - Arbre 2 : [48, 50] (affiché en sens inversé : 50 -> 48) avec continuation 52.
      - Arbre 3 : [48, 50, 52] (affiché en sens inversé : 52 -> 50 -> 48) avec continuation 53.
    """
    def __init__(self, silence_threshold=2.0):
        self.roots = {}         # Dictionnaire : clé = racine, valeur = arbre linéaire (PrefixTreeNode)
        self.sequences = []     # Liste des séquences enregistrées (listes de notes)
        self.silence_threshold = silence_threshold

    def train(self, sequence):
        """
        Entraîne l'arbre avec une séquence (liste de tuples (note, durée)). 
        Seules les hauteurs sont utilisées.
        Pour chaque k de 1 à len(sequence)-1, on extrait le préfixe = sequence[0:k]
        et la continuation = sequence[k].
        Le préfixe est renversé pour obtenir une branche linéaire dont la racine est le premier élément
        du préfixe inversé.
        """
        # Extraction des hauteurs
        notes = [note for note, dur in sequence]
        self.sequences.append(notes)

        # Pour chaque préfixe commençant au début et se terminant à l'index k-1, avec continuation notes[k]
        for k in range(1, len(notes)):
            prefix = notes[:k]           # Préfixe de longueur k (du début)
            cont = notes[k]              # La note qui suit ce préfixe
            rev_prefix = prefix[::-1]    # Inversion du préfixe pour obtenir la branche linéaire

            # La racine de l'arbre pour ce préfixe est le premier élément de rev_prefix
            root_note = rev_prefix[0]
            if root_note not in self.roots:
                self.roots[root_note] = PrefixTreeNode()
            node = self.roots[root_note]

            # Parcourir rev_prefix (à partir du deuxième élément)
            for note in rev_prefix[1:]:
                if node.child is None:
                    node.child = PrefixTreeNode()
                node = node.child
                # On ne modifie pas la continuation si elle existe déjà

            # Définir la continuation unique pour cette branche, si elle n'est pas déjà définie
            if node.continuation is None:
                node.continuation = cont

    def display_memory(self):
        """Affiche la mémoire sous forme d'arbres préfixés linéaires distincts."""
        print("\n?? **Arbres préfixés - Mémoire des séquences enregistrées**")
        for root_note, root in self.roots.items():
            print(f"\n?? Racine : {root_note}")
            self.display_tree(root, [root_note], level=1)

    def display_tree(self, node, branch, level):
        indent = "    " * level
        if node.continuation is not None:
            print(f"{indent}{' -> '.join(map(str, branch))} [ {node.continuation} ]")
        else:
            print(f"{indent}{' -> '.join(map(str, branch))}")
        if node.child is not None:
            # Puisque l'arbre est linéaire, il n'y a qu'un seul enfant
            self.display_tree(node.child, branch + [node.child.continuation if node.child.continuation is not None else ""], level+1)

    def generate(self, seed, length=10):
        """
        Génère une continuation monophonique.
        Pour le seed, on utilise la séquence enregistrée. On choisit l'arbre correspondant
        à la racine égale au premier élément du seed inversé (c'est-à-dire la dernière note du préfixe d'origine).
        """
        if not self.sequences:
            print("?? Aucun apprentissage disponible, génération impossible.")
            return []
        
        # On utilise le seed comme la séquence enregistrée (seules les hauteurs)
        generated = [note for note, dur in seed]
        # Choix de l'arbre : la racine doit être le premier élément du seed inversé
        # Pour la première séquence [48, 50, 52, 53], le seed devrait être [48, 50, 52, 53].
        # La branche correspondante sera construite à partir du préfixe [48,50,52] (avec continuation 53)
        # Ainsi, le seed d'entrée doit être traité comme la séquence entière.
        # On recherche l'arbre dont la racine est le premier élément du préfixe inversé, c'est-à-dire:
        # pour le préfixe [48,50,52] inversé = [52,50,48], la racine est 52.
        # Ainsi, nous choisissons le root = generated[-1] (la dernière note) pour générer la continuation.
        root_note = generated[-1]
        if root_note not in self.roots:
            print("?? Aucun arbre correspondant trouvé, génération impossible.")
            return []
        node = self.roots[root_note]
        branch = [root_note]
        for _ in range(length):
            if node.child is not None and node.child.continuation is not None:
                next_note = node.child.continuation
                generated.append(next_note)
                branch.append(next_note)
                node = node.child
            else:
                print("?? Fin de la branche, génération terminée.")
                break
        print("\n?? **Continuation générée**:")
        print("??", " -> ".join(map(str, generated)))
        return generated

    def play_midi_output(self, notes):
        """Simule la lecture MIDI en affichant la séquence générée."""
        print("\n[PLAY MIDI OUTPUT]")
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

    # Simuler un silence
    time.sleep(2)

    # Séquence 2 : [48, 50, 50, 52] (Do, Ré, Ré, Mi)
    sequence2 = [(48, 0.5), (50, 0.5), (50, 0.5), (52, 0.5)]
    print("\n=== Entraînement avec la séquence 2 : Do, Ré, Ré, Mi (48, 50, 50, 52) ===")
    continuator.train(sequence2)
    continuator.display_memory()
    print("\n=== Génération pour la séquence 2 ===")
    continuation2 = continuator.generate(sequence2, length=10)
    print("Continuation générée :", continuation2)

    # Fin du mode test.
