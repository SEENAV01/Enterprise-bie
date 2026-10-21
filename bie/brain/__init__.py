"""BIE's brain: the vision rulebook, the section runner and the sections built on it.

Every section works the same way (``runner.SectionRunner``): the maker AI gets the section's
instructions with Navin's vision rules and the source, writes brief notes and its output; BIE's code
checks it; an independent reviewer AI on another provider checks it against the source and the
rulebook; the maker remakes it with those findings; every round is kept as a process record.
"""
