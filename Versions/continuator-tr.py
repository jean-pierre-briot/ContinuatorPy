#!/usr/bin/python
# -*- coding: latin-1 -*-

import mido
mido.set_backend('mido.backends.rtmidi')
print('mido.get_output_names(): ' + str(mido.get_output_names()))

import random
import time
from collections import defaultdict
# from mido import MidiInput, MidiOutput, get_input_names, get_output_names
from mido import open_input, open_output, get_input_names, get_output_names

_note_default_duration = 250
_limit_generated_notes = 20
        
class MarkovMIDIContinuatorRealtime:
    def __init__(self, order=2, silence_threshold=2.0):
        self.order = order  # Taille du contexte (Markov d'ordre N)
        self.silence_threshold = silence_threshold  # Temps avant de générer la continuation
        self.model = defaultdict(list)
        self.last_note_time = time.time()
        self.recorded_notes = []

    def train(self, sequence):
        """Entraîne le modèle avec une séquence de notes (en temps réel)."""
#      print('train: sequence: ' + str(sequence))
        for i in range(len(sequence) - self.order):
            context = tuple(sequence[i:i+self.order])  # Contexte (notes, durées)
            next_note = sequence[i + self.order]
#          print('train: next_note: ' + str(next_note))
            self.model[context].append(next_note)
#        print('train: self.model: ' + str(self.model))

    def generate(self, seed, length=50):
        """Génère une suite de notes en temps réel."""
        if len(seed) < self.order:
            return []
        generated = list(seed)
#      print('generate: generated: ' + str(generated))
        for _ in range(length):
            context = tuple(generated[-self.order:])         
#          print('generate: context: ' + str(context))
#          print('generate: self.model: ' + str(self.model))           
            if context in self.model:
                next_note = random.choice(self.model[context])                
#              print('generate: next_note: ' + str(next_note))    
                generated.append(next_note)
            elif len(generated) >= _limit_generated_notes:  # Par exemple, 20 notes max
                print("Limite atteinte, retour à l'écoute.")
                break
            else:
#              print('generate: break')
                break  # Fin si plus de contexte connu
        return generated

    def play_midi_output(self, port_name, notes):
        """Envoie les notes MIDI en temps réel."""
#      with MidiOutput(port_name) as output:
        with open_output(port_name) as output:
            for note, duration in notes:
                output.send(mido.Message('note_on', note=note, velocity=64))
                time.sleep(duration / 1000)  # Convertir ticks MIDI en secondes
                output.send(mido.Message('note_off', note=note, velocity=64))

    def listen_and_continue(self, input_port, output_port):
        """Écoute le flux MIDI et génère la continuation lorsque le musicien s'arrête."""
#      with MidiInput(input_port) as inport, MidiOutput(output_port) as outport:
        with open_input(input_port) as inport, open_output(output_port) as outport:
            print(f"Écoute en cours sur : {input_port}")
            while True:
                for msg in inport.iter_pending():
                    if msg.type == 'note_on' and msg.velocity > 0:
                         self.recorded_notes.append((msg.note, time.time() - self.last_note_time))
                         self.last_note_time = time.time()
                    elif msg.type in ['note_off', 'note_on'] and msg.velocity == 0:
                        self.last_note_time = time.time()
                # Vérification du silence
                if self.recorded_notes and (time.time() - self.last_note_time > self.silence_threshold):
                    print("Silence détecté, génération de la continuation...")          
#                  print('listen_and_continue: self.recorded_notes: ' + str(self.recorded_notes))            
                    new_self_recorded_notes = []
                    for i in range(len(self.recorded_notes)):
                         new_self_recorded_notes.append((self.recorded_notes[i][0], _note_default_duration))
                    self.recorded_notes = new_self_recorded_notes
#                  print('listen_and_continue: self.recorded_notes: ' + str(self.recorded_notes))
                    self.train(self.recorded_notes)  # Apprentissage du style du musicien
                    seed = self.recorded_notes[-self.order:]                   
#                  print('listen_and_continue: seed: ' + str(seed))
                    generated_sequence = self.generate(seed, length=50)
                    self.play_midi_output(output_port, generated_sequence)
                    self.recorded_notes = []  # Réinitialisation
                time.sleep(0.01)  # Évite de monopoliser le CPU

# Liste des ports MIDI disponibles
print('Ports MIDI disponibles : ' + str(get_input_names()))

# Sélection des ports (modifiez en fonction de votre instrument)
input_port = "Nouvel appareil externe"  # Remplacez par le bon port si besoin
output_port = "Nouvel appareil externe"

# Lancement du continuateur en temps réel
continuator = MarkovMIDIContinuatorRealtime(order=2)
continuator.listen_and_continue(input_port, output_port)