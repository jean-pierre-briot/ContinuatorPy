Hello!
Thank you for your interest.

This is a reimplementation in Python of the Continuator from François Pachet.
His original implementation (in 2002, in Java) had unfortunately been lost. I tried to reimplement the Continuator from the informations in his publication:
Pachet, François, The Continuator: Musical Interaction with Style, Journal of New Music Research, Volume 32, Issue 3, Pages 333-341, 2003.
https://web.media.mit.edu/~rebklein/downloads/papers/jnmr%25252E32%25252E3%25252E333%25252E16861.pdf

I thank François for his continuous feedback.
François has since programmed his own new version in Python with some additional features (notably, a web interface and some constraint enforcing system based on belief propagation).
See: https://github.com/fpachet/continuator

The heart of the system is a representation of sequences of notes through prefixed trees, representing possible reversed sequences of notes, the root of tree representing the last played note and for each node (note) is attached the list of possible continuations (notes).
These trees are constructed and updated interactively while parsing a sequence of notes having been played.
The reversed representation allows an efficient parsing (to generate a continuation sequence) by traversing a tree (starting with the root note corresponding to the last note having been played) and searching for the longest (variable order Markov model) the longest sequence matching the input (having been played) sequence.
The next note of a continuation is chosen (sampled) between the list of possible continuations, with corresponding probabilities (Markov transition model) depending on the number of occurrences of each continuation note.
When generating the next note of the continuation, this note is appended to the input (having been played) notes and the matching process continues, this time starting with this new last note.
The main loop is a listen, generate and continue loop. Once the player stops playing, the Continuator starts generating a continuation corresponding to the sequence of notes having played. It does it note by note (or MIDI event by MIDI event in the case of the polyphonic version), in order to let the process to be stopped by the player restarting to play.

There are two versions:
- monophonic (considering individual notes): continuator-mono.py
- polyphonic (considering simultaneous notes, including chords): continuator-poly.py
The polyphonic version subsumes the monophonic version, but the monophonic version is little simpler to understand and may be sufficient in some cases.

The main difference between both versions is that the polyphonic version records the delta between a note starting time and previous note starting time, thus being able to reproduce the overlapping between notes. Main loop goes on MIDI event by MIDI event (and not, note by note, as in the monophonic version), in order to manage overlapping notes and possible interruptions by the player restarting to play.

There are three output modes:
- RealTime, the main one, with the Continuator infinitely listening to the player and generating a continuation.
- File, where the input sequence as well as the corresponding output continuation sequence are from MIDI files.
- Batch, some simplified version, with some predefined input sequence of notes pitches, for testing and illustrating the process of construction of the trees.

When starting the Continuator, the PreMemory.pickle file (if existing) is used as initial memory (trees and continuation).
Conversely, when the Continuator finishes (after some threshold silence - no more playing from the user), the built memory is saved in the PostMemory.pickle file, thus being available for possible reuses (as initial memory).

This software may be extended with additional features, present in the original version by François (viewpoints, pitch region, bias, that we actually have also implemented). But our experiments so far show that this simpler (and more pedagogical) version in general is sufficient for interesting medical experiments. The main addition would be: an interface and a belief propagation model to enforce (a restricted set of) possible constraints. On this topic, see papers by François Pachet and Pierre Roy et al. about Markov constraints.

To run the Continuator, you need at first to import (download and install) the following additional (non default) Python libraries, with the corresponding commands:

python3 -m pip install time

python3 -m pip install mido

You also need some physical MIDI interface (and maybe to configurate it on your computer) for some instrument (e.g., a keyboard, or any MIDI-enabled instrument).

To run the software, run the command: python3 continuator-poly.py (or continuator-mono.poly)

Note that there are several hyper-parameters (for configuration), e.g., if the Continuator will consider or not transpositions (in all keys) of what has been played.
They are defined and commented in the beginning (#hyperparameters) of the file.

Please enjoy and any feedback welcome!

jean-pierre
