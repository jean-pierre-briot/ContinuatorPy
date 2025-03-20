#!/usr/bin/python
# -*- coding: latin-1 -*-

import time
import random

#hyperparameters

class PrefixTreeNode:
    """
    """
    def __init__(self):
        self.note = None
        self.children = None
        self.continuations = None

class PrefixTreeContinuator:
    """
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

        # Pour k variant de len(notes)-1 à 0 ( du n-1ème élément au premier de la séquence)
        print('Notes : ' + str(notes) + ' Length notes : ' + str(len(notes)))
#      for k in range(len(notes) - 1, -1 -1):		Does not work correctly ?!!
        k = len(notes) - 1
        while k > 0:
            prefix = notes[:k]         # Sous-séquence [s1, .. , sN-1]
            cont = notes[k]            # Continuation = sN
            rev_prefix = prefix[::-1]  # Inversion du préfixe : [sN-1, ..., s1]
            root_note = rev_prefix[0]  # La racine de cet arbre est sN-1
            print('Parsing k : ' + str(k) + ' rev_prefix : ' + str(rev_prefix) + ' root_note : ' + str(root_note) + ' continuation : ' + str(cont))
            print('Vérification si existe déjà un arbre de racine : ' + str(root_note))
            # Si cet arbre n'existe pas encore, le créer
            if root_note not in self.roots:
                print('Pas trouvé -> Création arbre de racine : ' + str(root_note) + ' pour sous-séquence : ' + str(prefix) + ' et continuation : ' + str(cont))
                node = PrefixTreeNode()
                self.roots[root_note] = node
                node.note = root_note
                node.continuations = [cont]
            else:
                print('Un arbre avec racine ' + str(root_note) + ' existe déjà')
                node = self.roots[root_note]
                node.continuations.append(cont)
  
            # Parcourir rev_prefix (à partir du 2ème élément)
            for note in rev_prefix[1:]:
                print('Parcours sous-séquence : ' + str(rev_prefix[1:]) + ' pour note : ' + str(note))
                if node.children is None:
                    print('Le noeud parent est sans fils')
                    new_child_node = PrefixTreeNode()
                    new_child_node.note = note
                    new_child_node.continuations = [cont]
                    node.children = [new_child_node]
                    print('Ajout fils : ' + str(note) + ' continuations : ' + str([cont]), end = " ")
                    node = new_child_node
                else:
                    node_exists = False
                    print('Le noeud parent a au moins un fils')
                    print('Recherche parmi les fils si un a pour note : ' + str(note))
                    for child_node in node.children:
                        if child_node.note == note:
                            print('Un fils a pour note : ' + str(note) + ' on lui rajoute la continuation : ' + str(cont))
                            child_node.continuations.append(cont)
                            node_exists = True
                            node = child_node	# on continue à traiter le reste de la séquence
                            print('On continue à traiter le reste de la séquence')
                            break
                    if not(node_exists):
                        print('Aucun des fils a pour note : ' + str(note))
                        new_child_node = PrefixTreeNode()
                        print('Création nouveau fils pour note : ' + str(note) + ' ajouté à la liste des fils du père')
                        new_child_node.note = note
                        new_child_node.continuations = [cont]
                        node.children.append(new_child_node)
#                        print('Ajout nouveau fils : ' + str(note) + ' continuations : ' + str([cont]), end = " ")
                        node = new_child_node	# on continue à traiter le reste de la séquence
            print('')	# Retour à la ligne
            print('On a fini de parser toute la séquence : ' + str(rev_prefix[1:]))
            print('Dictionnaire arbres : ' + str(self.roots))
            k = k - 1

    def display_memory(self):
        """Affiche l'ensemble des arbres préfixés construits."""
        print("\n?? **Arbres préfixés - Mémoire des séquences enregistrées**")
        print('Dictionnaire arbres : ' + str(self.roots))
        # Pour chaque arbre, on affiche la branche complète avec la continuation
        for root_note, root in self.roots.items():
            print('Visualisation arbre de racine : ' + str(root_note))
            self.print_tree(root)
#            print(f"\n?? Racine : {root_note}")
#            self.display_tree(root, [root_note], level=1)
            print('')	# Retour à la ligne

    def print_tree(self, racine):
        print('Noeud : note : ' + str(racine.note) + ' continuations : ' + str(racine.continuations), end = " ")
        if racine.children != None:
            for child in racine.children:
                self.print_tree(child)
        
    def display_tree(self, node, branch, level):
        print('Display_tree : note : ' + str(node.note) + ' continuations : ' + str(branch))
   #     indent = "    " * level
        # Affichage de la branche actuelle avec la continuation
#        if node.continuation is not None:
#        print(f"{indent}{' -> '.join(map(str, branch))} [ {node.continuations} ]")
#        else:
#            print(f"{indent}{' -> '.join(map(str, branch))}")
        print(str(node.note) + ' [' + str(node.continuations) + ']', end = " ")
#        if node.child is not None:
#            self.display_tree(node.child, branch + [node.child.continuations if node.child.continuations is not None else "?"], level+1)

    def generate(self, played_sequence, max_continuation_length=10):
        """
        """
        if not self.sequences:
            print("There is no tree in the memory with a root note matching last note of the played sequence, thus I cannot generate a continuation.")
            return []
        # Utiliser le seed complet (liste de tuples) pour extraire les notes
        input_sequence = [note for note, dur in played_sequence]
        print('input_sequence : '  + str(input_sequence))
        last_input_note = input_sequence[-1]
        continuations_sequence = []
        print('continuations_sequence : ' + str(continuations_sequence))
        for i in range(2, max_continuation_length):
            if last_input_note not in self.roots:
                print('?? Aucun arbre correspondant trouvé correspondant à note : ' + str(last_input_note) + ' génération impossible.')
                break
            else:
                print('Génération de la ' + str(i - 1) + 'ème note de la continuation à partir de la note : ' + str(last_input_note))
                current_node = self.roots[last_input_note]
                while current_node.children is not None: 		# and node.children.continuation is not None:  Est-ce possible ?
                    print('Génération index i : ' + str(i) + ' noeud : ' + str(current_node) + ' note : ' + str(current_node.note) + ' continuations : ' + str(current_node.continuations))
                    next_child = None
                    for child in current_node.children:		# choisir la branche qui correspond à la prochaine note de la séquence jouée si elle existe"
                        print('On cherche un noeud fils du noeud de note : ' + str(current_node.note) + ' avec pour note : ' + str(input_sequence[-i]))
                        if child.note == input_sequence[-i]:
                            next_child = child
                            print('On a trouvé un fils qui a la même note : ' + str(child.note))
                            break
                    if next_child == None:		# on n'a pas trouvé la note suivante de la séquence parmi les fils
                        continuations = current_node.continuations
                        print('Note pas trouvée parmi les fils. Stop recherche. On tire au sort parmi les continuations du noeud actuel (de note : ' + str(current_node.note) + ') : ' + str(continuations))
                        next_note = continuations[random.randint(0, len(continuations) - 1)]
                        print('Génération nouvelle note de continuation : ' + str(next_note))
                        input_sequence.append(next_note)
                        continuations_sequence.append(next_note)
                        print('continuations_sequence : ' + str(continuations_sequence))
                        last_input_note = next_note # : input_sequence[-1]
                        break
                    else:
                        if len(input_sequence) < i:
                            print('On a épuisé la séquence d''entrée')
                            break
                        else:
                            print('On continue la recherche de la précédente i : ' + str(i) + ' note jouée de la séquence : ' + str(input_sequence) + ' parmi les fils')
                            # S'il y en a !!!
                            print('On continue la recherche de la précédente note jouée : ' + str(input_sequence[-i]) + ' parmi les fils')
                            current_node = next_child
        print("?? Génération terminée.")
        print('continuations_sequence : ' + str(continuations_sequence))
        print('Continuation générée : ' + str(continuations_sequence))
        return continuations_sequence

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
    continuation1 = continuator.generate(sequence1, max_continuation_length=10)
    print("Continuation générée :", continuation1)

    # Simuler un silence (ici, on n'attend pas vraiment, on passe à la séquence 2)
    time.sleep(2)

    # Séquence 2 : [48, 50, 50, 52] (Do, Ré, Ré, Mi)
    sequence2 = [(48, 0.5), (50, 0.5), (50, 0.5), (52, 0.5)]
    print("\n=== Entraînement avec la séquence 2 : Do, Ré, Ré, Mi (48, 50, 50, 52) ===")
    continuator.train(sequence2)
    continuator.display_memory()

    print("\n=== Génération pour la séquence 2 ===")
    continuation2 = continuator.generate(sequence2, max_continuation_length=10)
    print("Continuation générée :", continuation2)
    
    # Simuler un silence (ici, on n'attend pas vraiment, on passe à la séquence 3)
    time.sleep(2)

    # Séquence 3 : [48, 50] (Do, Ré)
    sequence3 = [(48, 0.5), (50, 0.5)]
    print("\n=== Entraînement avec la séquence 3 : Do, Ré (48, 50) ===")
    continuator.train(sequence3)
    continuator.display_memory()

    print("\n=== Génération pour la séquence 3 ===")
    continuation3 = continuator.generate(sequence3, max_continuation_length=10)
    print("Continuation générée :", continuation3)
