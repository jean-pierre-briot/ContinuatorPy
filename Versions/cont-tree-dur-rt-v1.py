#!/usr/bin/python
# -*- coding: latin-1 -*-

import mido
import time
import random
from collections import defaultdict
from mido import open_input, open_output, get_input_names, get_output_names

#_note_default_duration = 250
_limit_generated_notes = 10

class PrefixTreeNode:
    """Représente un n½ud dans l'arbre préfixé."""
    def __init__(self):
        self.children = {}
        self.continuations = []

class PrefixTreeContinuatorRealtime:
    """Continuateur temps réel basé sur des arbres préfixés avec gestion du rythme."""
    def __init__(self, silence_threshold=2.0):
        self.root = PrefixTreeNode()
        self.sequences = []
        self.last_note_time = time.time()
        self.recorded_notes = []  # Liste de tuples (note, durée)
        self.silence_threshold = silence_threshold  # Temps avant génération

    def train(self, sequence):
        """Ajoute une séquence (notes + durées) à l'arbre."""
        seq_index = len(self.sequences)
        self.sequences.append(sequence)

        for start in range(len(sequence)):
            current_node = self.root
            for i in range(len(sequence) - 1, start - 1, -1):
                note = sequence[i]

                if note not in current_node.children:
                    current_node.children[note] = PrefixTreeNode()
                
                current_node = current_node.children[note]

                if seq_index not in current_node.continuations:
                    current_node.continuations.append(seq_index)

    def generate(self, seed, length=_limit_generated_notes):
        """Génère une continuation avec notes et durées."""
        generated = list(seed)

        for _ in range(length):
            current_node = self.root
            match_found = False
            for i in range(len(generated) - 1, -1, -1):
                note = generated[i]
                if note in current_node.children:
                    current_node = current_node.children[note]
                    match_found = True
                else:
                    break

            if match_found and current_node.continuations:
                seq_index = random.choice(current_node.continuations)
                next_note = self.sequences[seq_index][len(generated) % len(self.sequences[seq_index])]
                generated.append(next_note)
            else:
                break  # Arrêt si aucune continuation trouvée

        return generated

    def play_midi_output(self, port_name, notes):
        """Joue une séquence MIDI en respectant les durées."""
        with open_output(port_name) as output:
            for note, duration in notes:
                output.send(mido.Message('note_on', note=note, velocity=64))
                time.sleep(duration)  # Respecte la durée de la note
                output.send(mido.Message('note_off', note=note, velocity=64))

    def listen_and_continue(self, input_port, output_port):
        """Écoute les entrées MIDI et génère une continuation après un silence."""
        with open_input(input_port) as inport, open_output(output_port) as outport:
            print(f"Écoute en cours sur : {input_port}")

            while True:
                for msg in inport.iter_pending():
                    current_time = time.time()
                    if msg.type == 'note_on' and msg.velocity > 0:
                        duration = current_time - self.last_note_time  # Calcul de la durée
                        self.recorded_notes.append((msg.note, duration))
                        self.last_note_time = current_time

                    elif msg.type in ['note_off', 'note_on'] and msg.velocity == 0:
                        self.last_note_time = current_time

                # Vérifier le silence et générer une continuation
                if self.recorded_notes and (time.time() - self.last_note_time > self.silence_threshold):
                    print("Silence détecté, génération de la continuation...")
                    self.train(self.recorded_notes)  # Apprentissage en direct
                    seed = self.recorded_notes[-2:]  # Prendre les 2 dernières notes comme seed
                    generated_sequence = self.generate(seed, length=10)

                    self.play_midi_output(output_port, generated_sequence)
                    self.recorded_notes = []  # Réinitialisation

                time.sleep(0.01)  # Évite de monopoliser le CPU

# Liste des ports MIDI disponibles
print("Ports MIDI disponibles :", get_input_names())

# Sélection automatique des ports MIDI
input_port = get_input_names()[0]
output_port = get_output_names()[0]

# Lancement du continuateur en temps réel
continuator = PrefixTreeContinuatorRealtime()
continuator.listen_and_continue(input_port, output_port)
