#!/usr/bin/python
# -*- coding: latin-1 -*-

import mido
import time
import random
from mido import open_input, open_output, get_input_names, get_output_names

class PrefixTreeNode:
    """Représente un n½ud dans l'arbre préfixé monophonique."""
    def __init__(self):
        self.child = None  # Un seul fils (arbre linéaire)
        self.continuation = None  # Une seule continuation pour toute la branche

class PrefixTreeContinuator:
    """Continuateur monophonique basé sur un arbre préfixé conforme à la publication de François Pachet."""
    def __init__(self, silence_threshold=2.0):
        self.roots = {}  # Chaque arbre préfixé a sa propre racine
        self.sequences = []  
        self.last_note_time = time.time()
        self.recorded_notes = []  
        self.silence_threshold = silence_threshold

    def train(self, sequence):
        """
        Ajoute une séquence à l'arbre préfixé en garantissant que chaque arbre est linéaire.
        - Chaque séquence crée un arbre distinct.
        - Chaque n½ud a un seul fils (structure linéaire).
        - Chaque branche complète partage la même continuation.
        """
        notes = [note[0] for note in sequence]  
        self.sequences.append(notes)

        # Construction des arbres linéaires
        for start in range(len(notes) - 1):
            root_note = notes[start + 1]  # La racine de l'arbre est la note suivante
            if root_note not in self.roots:
                self.roots[root_note] = PrefixTreeNode()
            current_node = self.roots[root_note]

            # Construire la branche linéaire
            for i in range(start, -1, -1):
                note = notes[i]
                if current_node.child is None:
                    current_node.child = PrefixTreeNode()
                current_node = current_node.child

            # Définir la continuation unique pour toute la branche
            if current_node.continuation is None:
                current_node.continuation = notes[-1]

        print(f"? Arbre mis à jour : {len(self.sequences)} séquences enregistrées.")
        self.display_memory()

    def display_memory(self):
        """Affiche une représentation de l?ensemble des arbres préfixés de manière distincte."""
        print("\n?? **Arbres préfixés - Mémoire des séquences enregistrées**")
        for root_note, root_node in self.roots.items():
            print(f"\n?? Racine : {root_note}")
            self.display_tree(root_node, [root_note], level=1)

    def display_tree(self, node, prefix, level):
        """Affiche un arbre préfixé spécifique avec indentation pour chaque niveau."""
        if node.child:
            indent = "    " * level
            continuation_display = f" [ {node.child.continuation} ]" if node.child.continuation else ""
            print(f"{indent}{' -> '.join(map(str, prefix))}{continuation_display}")
            self.display_tree(node.child, prefix + ["->"], level + 1)

    def generate(self, seed, length=10):
        """Génère une continuation monophonique en parcourant les arbres préfixés."""
        if not self.sequences:
            print("?? Aucun apprentissage disponible, génération impossible.")
            return []

        generated_notes = [note[0] for note in seed]
        root_note = generated_notes[-1]

        if root_note not in self.roots:
            print("?? Aucun arbre correspondant trouvé, génération impossible.")
            return []

        current_node = self.roots[root_note]

        for _ in range(length):
            if current_node.child and current_node.child.continuation:
                next_note = current_node.child.continuation
                generated_notes.append(next_note)
                current_node = current_node.child
            else:
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
