#!/usr/bin/python
# -*- coding: latin-1 -*-

import time
import random

#hyperparameters
_silence_threshold = 2.0
_max_continuation_length = 10

class PrefixTreeNode:
    def __init__(self):
        self.note = None
        self.children_list = None
        self.continuation_list = None

class PrefixTreeContinuator:
    def __init__(self):
        self.root_dictionary = {}

    def train(self, event_sequence):
        # event_sequence = [(<pitch>, <duration>), ... , (<pitch>, <duration>)]
        note_sequence = [note for note, dummy in event_sequence]
        # note_sequence: [<pitch>, ... , <pitch>]

        print('Notes : ' + str(note_sequence) + ' Lengths : ' + str(len(note_sequence)))
#       for k in range(len(note_sequence) - 1, -1 -1):		Does not work correctly ?!!
        i = len(note_sequence) - 1
        while i > 0:
            # i will vary from length-1 (pre-last element: note_n-1) to 0 (first element: note_1)
            # for k in range(len(note_sequence) - 1, -1 - 1): Does not work correctly (?)
            note_sub_sequence = note_sequence[:i]                   # Prefix Sub-sequence: [note_1, .. , note_i]
            continuation = note_sequence[i]                         # Continuation = note_i
            reversed_note_sub_sequence = note_sub_sequence[::-1]    # Reversed Sub-sequence: [note_i, ..., note_1]
            root_note = reversed_note_sub_sequence[0]               # Note of the root of the tree to be created: note_i
            print('Parsing k : ' + str(i) + ' reversed_note_sub_sequence : ' + str(reversed_note_sub_sequence) + ' root_note : ' + str(root_note) + ' continuation : ' + str(continuation))
            print('Vérification si existe déjà un arbre de racine : ' + str(root_note))
            if root_note not in self.root_dictionary:
                print('Pas trouvé -> Création arbre de racine : ' + str(root_note) + ' pour sous-séquence : ' + str(note_sub_sequence) + ' et continuation : ' + str(continuation))
                current_node = PrefixTreeNode()
                self.root_dictionary[root_note] = current_node
                current_node.note = root_note
                current_node.continuation_list = [continuation]
            else:
                print('Un arbre avec racine ' + str(root_note) + ' existe déjà')
                current_node = self.root_dictionary[root_note]
                current_node.continuation_list.append(continuation)

            for note in reversed_note_sub_sequence[1:]:
                print('Parcours sous-séquence : ' + str(reversed_note_sub_sequence[1:]) + ' pour note : ' + str(note))
                if current_node.children_list is None:
                    print('Le noeud parent est sans fils')
                    new_child_node = PrefixTreeNode()
                    new_child_node.note = note
                    new_child_node.continuation_list = [continuation]
                    current_node.children_list = [new_child_node]
                    print('Ajout fils : ' + str(note) + ' continuation_list : ' + str([continuation]), end = " ")
                    current_node = new_child_node
                else:
                    node_exists = False
                    print('Le noeud parent a au moins un fils')
                    print('Recherche parmi les fils si un a pour note : ' + str(note))
                    for child_node in current_node.children_list:
                        if child_node.note == note:
                            print('Un fils a pour note : ' + str(note) + ' on lui rajoute la continuation : ' + str(continuation))
                            child_node.continuation_list.append(continuation)
                            node_exists = True
                            current_node = child_node	# on continue à traiter le reste de la séquence
                            print('On continue à traiter le reste de la séquence')
                            break
                    if not(node_exists):
                        print('Aucun des fils n''a pour note : ' + str(note))
                        new_child_node = PrefixTreeNode()
                        print('Création nouveau fils pour note : ' + str(note) + ' ajouté à la liste des fils du père')
                        new_child_node.note = note
                        new_child_node.continuation_list = [continuation]
                        current_node.children_list.append(new_child_node)
#                       print('Ajout nouveau fils : ' + str(note) + ' continuation_list : ' + str([cont]), end = " ")
                        current_node = new_child_node	# on continue à traiter le reste de la séquence en descendant dans l'arbre
            print('')	# Retour à la ligne
            print('On a fini de parser toute la séquence : ' + str(reversed_note_sub_sequence[1:]))
            print('Dictionnaire arbres : ' + str(self.root_dictionary))
            i = i - 1

    def display_memory(self):
        print("Arbres préfixés - Mémoire des séquences enregistrées")
        print('Dictionnaire arbres : ' + str(self.root_dictionary))
        for root_note, root in self.root_dictionary.items():
            print('Visualisation arbre de racine : ' + str(root_note))
            self.print_tree(root)
            print('')	# Retour à la ligne

    def print_tree(self, racine):
        print('Node : note : ' + str(racine.note) + ' continuations : ' + str(racine.continuation_list), end = " ")
        if racine.children_list != None:
            for child in racine.children_list:
                self.print_tree(child)
        
    def display_tree(self, node, branch, level):
        print('Display_tree : note : ' + str(node.note) + ' continuation_list : ' + str(branch))
        print(str(node.note) + ' [' + str(node.continuation_list) + ']', end = " ")

    def generate(self, event_sequence):
        note_sequence = [note for note, dur in event_sequence]
        print('note_sequence : '  + str(note_sequence))
        last_input_note = note_sequence[-1]
        continuation_list = []
        print('continuation_list : ' + str(continuation_list))
        for i in range(2, _max_continuation_length):
            if last_input_note not in self.root_dictionary:
                print('?? Aucun arbre correspondant trouvé correspondant à note : ' + str(last_input_note) + ' génération impossible.')
                break
            else:
                print('Génération de la ' + str(i - 1) + 'ème note de la continuation à partir de la note : ' + str(last_input_note))
                current_node = self.root_dictionary[last_input_note]
                while current_node.children_list is not None: 		# and node.children_list.continuation is not None:  Est-ce possible ?
                    print('Génération index i : ' + str(i) + ' noeud : ' + str(current_node) + ' note : ' + str(current_node.note) + ' continuations : ' + str(current_node.continuation_list))
                    next_child = None
                    for child in current_node.children_list:		# choisir la branche qui correspond à la prochaine note de la séquence jouée si elle existe"
                        print('On cherche un noeud fils du noeud de note : ' + str(current_node.note) + ' avec pour note : ' + str(note_sequence[-i]))
                        if child.note == note_sequence[-i]:
                            next_child = child
                            print('On a trouvé un fils qui a la même note : ' + str(child.note))
                            break
                    if next_child == None:		# on n'a pas trouvé la note suivante de la séquence parmi les fils
                        continuation_list = current_node.continuation_list
                        print('Note pas trouvée parmi les fils. Stop recherche. On tire au sort parmi les continuations du noeud actuel (de note : ' + str(current_node.note) + ') : ' + str(continuation_list))
                        next_note = continuation_list[random.randint(0, len(continuation_list) - 1)]
                        print('Génération nouvelle note de continuation : ' + str(next_note))
                        note_sequence.append(next_note)
                        continuation_list.append(next_note)
                        print('continuation_list : ' + str(continuation_list))
                        last_input_note = next_note     # : note_sequence[-1]
                        break
                    else:
                        if len(note_sequence) < i:
                            print('On a épuisé la séquence d''entrée')
                            break
                        else:
                            print('On continue la recherche de la précédente i : ' + str(i) + ' note jouée de la séquence : ' + str(note_sequence) + ' parmi les fils')
                            # S'il y en a !!!
                            print('On continue la recherche de la précédente note jouée : ' + str(note_sequence[-i]) + ' parmi les fils')
                            current_node = next_child
        print("?? Génération terminée.")
        print('Continuation générée : ' + str(continuation_list))
        return continuation_list

    def play_output(self, note_list):
        """Simule la lecture MIDI en affichant la séquence générée."""
        print("\n[PLAY OUTPUT]")
        print("Notes jouées :", " -> ".join(map(str, note_list)))

# ------------------- Mode Test -------------------
if __name__ == '__main__':
    continuator = PrefixTreeContinuator()

    # Séquence 1 : [48, 50, 52, 53] (Do, Ré, Mi, Fa)
    sequence1 = [(48, 0.5), (50, 0.5), (52, 0.5), (53, 0.5)]
    print("=== Entraînement avec la séquence 1 : Do, Ré, Mi, Fa (48, 50, 52, 53) ===")
    continuator.train(sequence1)
    continuator.display_memory()

    print("\n=== Génération pour la séquence 1 ===")
    continuation1 = continuator.generate(sequence1)
    print("Continuation générée :", continuation1)

    # Simuler un silence (ici, on n'attend pas vraiment, on passe à la séquence 2)
    time.sleep(2)

    # Séquence 2 : [48, 50, 50, 52] (Do, Ré, Ré, Mi)
    sequence2 = [(48, 0.5), (50, 0.5), (50, 0.5), (52, 0.5)]
    print("\n=== Entraînement avec la séquence 2 : Do, Ré, Ré, Mi (48, 50, 50, 52) ===")
    continuator.train(sequence2)
    continuator.display_memory()

    print("\n=== Génération pour la séquence 2 ===")
    continuation2 = continuator.generate(sequence2)
    print("Continuation générée :", continuation2)
    
    # Simuler un silence (ici, on n'attend pas vraiment, on passe à la séquence 3)
    time.sleep(2)

    # Séquence 3 : [48, 50] (Do, Ré)
    sequence3 = [(48, 0.5), (50, 0.5)]
    print("\n=== Entraînement avec la séquence 3 : Do, Ré (48, 50) ===")
    continuator.train(sequence3)
    continuator.display_memory()

    print("\n=== Génération pour la séquence 3 ===")
    continuation3 = continuator.generate(sequence3)
    print("Continuation générée :", continuation3)
