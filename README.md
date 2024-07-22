# cpycvt
Python module to convert COBOL copybooks to JSON or YAML

## Overview

This module takes a standard COBOL copybook and converts to JSON or YAML. Output
is a list of elements decoded by the parser. Optionally, the element list can
be converted to a nested format which more closely mirrors the structure of
a copybook.

## Command Line Usage

    usage: copybook.py [-h] [-output OUTPUT] [-yaml] [-nested] filename
    
    positional arguments:
      filename        name of input file
    
    options:
      -h, --help      show this help message and exit
      -output OUTPUT  output to specified filename
      -yaml           output type as YAML (default is JSON)
      -nested         output converted copybook as nested objects (default is flat)

 `filename`: the name of the copybook file. The parser expects the file in standard
format, i.e. the copybook beins at column 8, and columns 74 and above are not
read. Comments beginning with '*' at column 7 are permitted.

`output`: optionally writes the converted file to the filesystem. Default is
STDOUT.

`-yaml`: writes the output as YAML. Default is JSON.

`-nested`: writes the output in nested format. Default is flat.

## Sample

Convert copybook `sample`.cpy` to JSON and write to STDOUT:

    python copybook.py sample/sample1.cpy
