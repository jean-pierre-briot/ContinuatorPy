#!/usr/bin/python
# -*- coding: latin-1 -*-

import mido
import time
import random
from mido import open_input, open_output, get_input_names, get_output_names

class PrefixTreeNode:
    """Représente un n½ud dans l'arbre préfixé monophonique."""
    def __init__(self):
        self.children = {}
        self.continuations = []  # Liste des notes de continuation

class PrefixTreeContinuator:
    """Continuateur monophonique basé sur un arbre préfixé conforme à la publication de François Pachet."""
    def __init__(self, silence_threshold=2.0):
        self.root = PrefixTreeNode()
        self.sequences = []  
        self.last_note_time = time.time()
        self.recorded_notes = []  
        self.silence_threshold = silence_threshold

    def train(self, sequence):
        """
        Ajoute une séquence à l'arbre préfixé en fusionnant correctement les sous-arbres existants.
        La racine de chaque arbre correspond à la dernière note de la séquence mémorisée.
        """
        notes = [note[0] for note in sequence]  
        self.sequences.append(notes)

        # La racine de chaque sous-arbre est la dernière note de la séquence mémorisée
        root_note = notes[-1]
        if root_note not in self.root.children:
            self.root.children[root_note] = PrefixTreeNode()
        current_node = self.root.children[root_note]

        # Construire le reste de l'arbre en partant de la fin vers le début
        for i in range(len(notes) - 2, -1, -1):  
            note = notes[i]
            if note not in current_node.children:
                current_node.children[note] = PrefixTreeNode()
            current_node = current_node.children[note]

        # Ajouter la continuation (prochaine note après ce préfixe)
        if len(notes) > 1 and notes[-1] not in current_node.continuations:
            current_node.continuations.append(notes[-1])

        print(f"? Arbre mis à jour : {len(self.sequences)} séquences enregistrées.")
        self.display_memory()

    def display_memory(self, node=None, prefix=[], level=0, is_first_child=True):
        """Affiche une représentation de l?arbre préfixé monophonique avec indentation améliorée."""
        if node is None:
            node = self.root
            print("\n?? **Arbre préfixé - Mémoire des séquences enregistrées**")
        
        for i, (note, child) in enumerate(node.children.items()):
            indent = "    " * (level - 1) + ("-> " if level > 0 and i > 0 else "")  # Ajustement pour plusieurs branches
            branch_prefix = "-> " if level > 0 and i == 0 and not is_first_child else ""
            print(f"{indent}{branch_prefix}{' -> '.join(map(str, prefix + [note]))}  | Continuations: {child.continuations}")
            self.display_memory(child, prefix + [note], level + 1, is_first_child=False)

    def generate(self, seed, length=10):
        """Génère une continuation monophonique en parcourant l'arbre préfixé."""
        if not self.sequences:
            print("?? Aucun apprentissage disponible, génération impossible.")
            return []

        generated_notes = [note[0] for note in seed]

        for _ in range(length):
            current_node = self.root
            match_found = False
            for i in range(len(generated_notes), 0, -1):
                sub_prefix = generated_notes[-i:]
                temp_node = self.root
                valid = True
                for note in sub_prefix:
                    if note in temp_node.children:
                        temp_node = temp_node.children[note]
                    else:
                        valid = False
                        break
                if valid and temp_node.continuations:
                    next_note = random.choice(temp_node.continuations)
                    generated_notes.append(next_note)
                    match_found = True
                    break
            if not match_found:
                print("?? Aucun préfixe exact trouvé, fin de la génération.")
                break

        print("\n?? **Continuation générée**:")
        print("??", " -> ".join(map(str, generated_notes)))
        return generated_notes

    def play_midi_output(self, port_name, notes):
        """Joue une séquence MIDI monophonique."""
        with open_output(port_name) as output:
            for note in notes:
                output.send(mido.Message('note_on', note=note, velocity=64))
                time.sleep(0.5)  
                output.send(mido.Message('note_off', note=note, velocity=64))

    def listen_and_continue(self, input_port, output_port):
        """Écoute le flux MIDI et génère une continuation après un silence."""
        with open_input(input_port) as inport, open_output(output_port) as outport:
            print(f"?? Écoute en cours sur : {input_port}")
            while True:
                for msg in inport.iter_pending():
                    current_time = time.time()
                    if msg.type == 'note_on' and msg.velocity > 0:
                        self.recorded_notes.append((msg.note, current_time - self.last_note_time))
                        self.last_note_time = current_time
                    elif msg.type == 'note_off':
                        self.last_note_time = current_time

                silence_duration = time.time() - self.last_note_time
                if self.recorded_notes and silence_duration > self.silence_threshold:
                    print("?? Silence détecté, génération de la continuation...")
                    self.train(self.recorded_notes)
                    seed = self.recorded_notes[-2:]  
                    generated_sequence = self.generate(seed, length=10)
                    if generated_sequence:
                        self.play_midi_output(output_port, generated_sequence)
                    else:
                        print("?? Échec de la génération, pas assez de données.")
                    self.recorded_notes = []
                time.sleep(0.01)

# Affichage et sélection des ports MIDI
print("?? Ports MIDI disponibles :", get_input_names())
input_port = get_input_names()[0]
output_port = get_output_names()[0]

# Lancement du continuateur monophonique
continuator = PrefixTreeContinuator(silence_threshold=2.0)
continuator.listen_and_continue(input_port, output_port)
