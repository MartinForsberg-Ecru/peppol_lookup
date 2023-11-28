# peppol_lookup

Takes a text-file with a list of participant ids as input. Currenctly only schemeid 0007 and 0088 is supported (deduced by the length of the identifier).

The script handles duplicates in the list (only checks once for each unique identifier).

The output is a new text file with a participant information. The lines are mapped one-to-one, meaning that the output has exactly the amount of lines as the input file had.

