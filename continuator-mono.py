#from packaging.tags import PythonVersion

#!/usr/bin/python
# -*- coding: Unicode -*-

# Continuator in Python
# Version 1.3.1
# Versions/dates: current: 17/08/2025; first: 27/02/2025
# Monophonic, a simple adaptation of Polyphonic version
# Jean-Pierre Briot

# This is a reimplementation in Python of the Continuator from Francois Pachet.
# His original implementation (in 2002, in Java) had unfortunately been lost.
# I tried to reimplement the Continuator from the informations in his publication:
# Pachet, Francois, The Continuator: Musical Interaction with Style, Journal of New Music Research, Volume 32, Issue 3, Pages 333-341, 2003.
# Thanks to Francois for his continuous feedback.

with open("continuator-poly.py", "r") as continuator_poly_file:
    continuator_poly_code = continuator_poly_file.read()
    exec(continuator_poly_code)

def mono_generate(self, note_sequence):
    return self.generate_note_sequence(note_sequence)

PrefixTreeContinuator.generate = mono_generate

# To run it:
# continuator = PrefixTreeContinuator()
# continuator.run('RealTime')
