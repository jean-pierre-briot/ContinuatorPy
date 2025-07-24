Hello!
Thank you for your interest.

This is a reimplementation in Python of the Continuator from François Pachet.
His original implementation (in 2002, in Java) had unfortunately been lost. I tried to reimplement the Continuator from the informations in his publication:
Pachet, François, The Continuator: Musical Interaction with Style, Journal of New Music Research, Volume 32, Issue 3, Pages 333-341, 2003.
https://web.media.mit.edu/~rebklein/downloads/papers/jnmr%25252E32%25252E3%25252E333%25252E16861.pdf

I thank François for his continuous feedback.

There are two versions:
monophonic: continuator-mono.py
polyphonic: continuator-poly.py

You need at first to import (download and install) the following additional (non default) Python libraries, with the corresponding commands:

python3 -m pip install time

python3 -m pip install mido

You also need some physical MIDI interface (and maybe to configurate it on your computer) for some instrument (e.g., a keyboard, or any MIDI-enabled instrument).

To run the software, run the command: python3 continuator-*.py

Note that there are several hyper-parameters (for configuration), e.g., if the Continuator will consider or not transpositions (in all keys) of what has been played.
Theye are defined and commented in the beginning (#hyperparameters) of the file.

Please enjoy and any feedback welcome!

jean-pierre
