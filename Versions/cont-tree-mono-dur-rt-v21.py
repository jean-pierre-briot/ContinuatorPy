#!/usr/bin/python
# -*- coding: latin-1 -*-

import time
import random

# Nous utilisons ici la version monophonique correcte avec arbres préfixés linéaires.
# Ce code est basé sur l'algorithme de François Pachet.

class PrefixTreeNode:
    """Représente un n½ud dans l'arbre préfixé monophonique."""
    def __init__(self):
        self.children = {}
        self.continuation = None  # Une seule continuation pour toute la branche

class PrefixTreeContinuator:
    """
    Continuateur monophonique basé sur un arbre préfixé conforme à la publication de François Pachet.
    
    Après l'écoute d'une séquence, par exemple [48, 50, 52, 53] (Do, Ré, Mi, Fa),
    la mémoire doit contenir exactement trois arbres distincts :
        - Racine : 52
            52 -> 50 -> 48 [53]
        - Racine : 50
            50 -> 48 [52]
        - Racine : 48
            48 [50]
    """
    def __init__(self, silence_threshold=2.0):
        self.roots = {}   # Chaque arbre préfixé a sa propre racine (clé = note)
        self.sequences = []  
        self.last_note_time = time.time()
        self.recorded_notes = []  
        self.silence_threshold = silence_threshold

    def train(self, sequence):
        """
        Entraîne l'arbre avec une séquence (liste de tuples (note, durée)).
        On ne considère que les hauteurs.
        Pour une séquence [A, B, C, D], on doit créer trois arbres distincts :
            - Arbre de racine C : [C -> B -> A] avec continuation D
            - Arbre de racine B : [B -> A] avec continuation C
            - Arbre de racine A : [A] avec continuation B
        """
        notes = [note for note, dur in sequence]
        self.sequences.append(notes)

        # Pour chaque sous-séquence débutant à index 0 et finissant à index (k) (k de 1 à len(notes)-1)
        # on associe la note à l'index k comme continuation.
        for k in range(1, len(notes)):
            # La racine de l'arbre pour cette sous-séquence est la note à l'index 0
            # mais nous voulons que la structure soit linéaire à partir du début.
            # Selon la publication, pour une séquence [A, B, C, D] :
            # - l'arbre correspondant à [A] a continuation B,
            # - celui correspondant à [A, B] a continuation C,
            # - celui correspondant à [A, B, C] a continuation D.
            # Ainsi, nous construisons uniquement ces arbres en partant du début.
            prefix = notes[:k]  # sous-séquence de A jusqu'à la note d'index k-1
            continuation = notes[k]  # la note qui suit cette sous-séquence

            # La racine pour cet arbre sera la première note de la sous-séquence.
            root_note = prefix[0]
            if root_note not in self.roots:
                self.roots[root_note] = PrefixTreeNode()
            current_node = self.roots[root_note]

            # Construire la branche linéaire pour cette sous-séquence
            # On parcourt le préfixe du deuxième élément à la fin.
            for note in prefix[1:]:
                if note not in current_node.children:
                    current_node.children[note] = PrefixTreeNode()
                current_node = current_node.children[note]

            # Une fois la branche construite, définir la continuation unique.
            # Pour éviter les doublons, si une continuation est déjà définie, on la laisse.
            if current_node.continuation is None:
                current_node.continuation = continuation

        print(f"? Arbre mis à jour : {len(self.sequences)} séquences enregistrées.")
        self.display_memory()

    def display_memory(self):
        """Affiche la mémoire sous forme d'arbres préfixés distincts, avec indentation pour chaque branche."""
        print("\n?? **Arbres préfixés - Mémoire des séquences enregistrées**")
        for root_note, root_node in self.roots.items():
            print(f"\n?? Racine : {root_note}")
            self.display_tree(root_node, [root_note], level=1)

    def display_tree(self, node, prefix, level):
        indent = "    " * level
        if node.continuation is not None:
            print(f"{indent}{' -> '.join(map(str, prefix))} [ {node.continuation} ]")
        else:
            print(f"{indent}{' -> '.join(map(str, prefix))}")
        for note, child in node.children.items():
            self.display_tree(child, prefix + [note], level + 1)

    def generate(self, seed, length=10):
        """
        Génère une continuation monophonique en se basant sur les arbres préfixés.
        Pour le seed, on utilisera la séquence enregistrée.
        """
        if not self.sequences:
            print("?? Aucun apprentissage disponible, génération impossible.")
            return []

        generated_notes = [note for note, dur in seed]
        # Utiliser la dernière note du seed pour choisir l'arbre correspondant.
        root_note = generated_notes[0]  # Ici, la racine est la première note du seed.
        if root_note not in self.roots:
            print("?? Aucun arbre correspondant trouvé, génération impossible.")
            return []

        current_node = self.roots[root_note]
        for _ in range(length):
            if current_node.continuation is not None:
                next_note = current_node.continuation
                generated_notes.append(next_note)
                # Si le prochain_note existe comme enfant, on descend dans l'arbre
                if next_note in current_node.children:
                    current_node = current_node.children[next_note]
                else:
                    break
            else:
                print("?? Fin de la branche, génération terminée.")
                break

        print("\n?? **Continuation générée**:")
        print("??", " -> ".join(map(str, generated_notes)))
        return generated_notes

    def play_midi_output(self, port_name, notes):
        """Joue une séquence MIDI monophonique.
           (Ici, on simule simplement l'impression de la séquence.)
        """
        print("\n[PLAY MIDI OUTPUT]")
        print("Notes jouées :", " -> ".join(map(str, notes)))
        # Code MIDI réel (à décommenter lorsque le clavier sera disponible)
        # with open_output(port_name) as output:
        #     for note in notes:
        #         output.send(mido.Message('note_on', note=note, velocity=64))
        #         time.sleep(0.5)
        #         output.send(mido.Message('note_off', note=note, velocity=64))

    # La partie d'écoute réelle via MIDI est conservée en commentaires :
    # def listen_and_continue(self, input_port, output_port):
    #     with open_input(input_port) as inport, open_output(output_port) as outport:
    #         print(f"?? Écoute en cours sur : {input_port}")
    #         while True:
    #             for msg in inport.iter_pending():
    #                 current_time = time.time()
    #                 if msg.type == 'note_on' and msg.velocity > 0:
    #                     self.recorded_notes.append((msg.note, current_time - self.last_note_time))
    #                     self.last_note_time = current_time
    #                 elif msg.type == 'note_off':
    #                     self.last_note_time = current_time
    #
    #             silence_duration = time.time() - self.last_note_time
    #             if self.recorded_notes and silence_duration > self.silence_threshold:
    #                 print("?? Silence détecté, génération de la continuation...")
    #                 self.train(self.recorded_notes)
    #                 seed = self.recorded_notes[-2:]
    #                 generated_sequence = self.generate(seed, length=10)
    #                 if generated_sequence:
    #                     self.play_midi_output(output_port, generated_sequence)
    #                 else:
    #                     print("?? Échec de la génération, pas assez de données.")
    #                 self.recorded_notes = []
    #             time.sleep(0.01)

# ------------------- Test Mode -------------------
if __name__ == '__main__':
    # Création du continuateur
    continuator = PrefixTreeContinuator(silence_threshold=2.0)

    # Séquence 1 : [48, 50, 52, 53] correspond à Do, Ré, Mi, Fa.
    sequence1 = [(48, 0.5), (50, 0.5), (52, 0.5), (53, 0.5)]
    print("=== Entraînement avec la séquence 1 : Do, Ré, Mi, Fa (48, 50, 52, 53) ===")
    continuator.train(sequence1)

    # On affiche la mémoire des arbres préfixés
    continuator.display_memory()

    # Génération de la continuation pour la séquence 1
    print("\n=== Génération de la continuation pour la séquence 1 ===")
    continuation1 = continuator.generate(sequence1, length=10)
    print("Continuation générée :", continuation1)

    # Simuler un silence et une deuxième séquence.
    time.sleep(2)  # Simuler le silence

    # Séquence 2 : [48, 50, 50, 52] correspond à Do, Ré, Ré, Mi.
    sequence2 = [(48, 0.5), (50, 0.5), (50, 0.5), (52, 0.5)]
    print("\n=== Entraînement avec la séquence 2 : Do, Ré, Ré, Mi (48, 50, 50, 52) ===")
    continuator.train(sequence2)

    # Affichage mis à jour de la mémoire
    continuator.display_memory()

    # Génération de la continuation pour la séquence 2
    print("\n=== Génération de la continuation pour la séquence 2 ===")
    continuation2 = continuator.generate(sequence2, length=10)
    print("Continuation générée :", continuation2)

    # Fin du mode test.
