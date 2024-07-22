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

sample1.cpy

    000001 10 RECORD-01.
    000002    20 RECORD-02.
    000003       30 ACTION-DATE.
    000004          40 ACTION-DATE-YEAR-CC.
    000005             60 ACTION-DATE-CENT             PIC 99.
    000006             60 ACTION-DATE-YEAR             PIC 99.
    000007          40 ACTION-DATE-MONTH               PIC 99.
    000008          40 ACTION-DATE-DAY                 PIC 99.

Convert copybook `sample`.cpy` to JSON and write to STDOUT:

    python copybook.py sample/sample1.cpy

Output:

    {
      "nodes": [
        {
          "RECORD-01": {
            "level": 10,
            "type": "record"
          }
        },
        {
          "RECORD-02": {
            "level": 20,
            "type": "record"
          }
        },
        {
          "ACTION-DATE": {
            "level": 30,
            "type": "record"
          }
        },
        {
          "ACTION-DATE-YEAR-CC": {
            "level": 40,
            "type": "record"
          }
        },
        {
          "ACTION-DATE-CENT": {
            "level": 60,
            "length": 2,
            "type": "numeric",
            "signed": false
          }
        },
        {
          "ACTION-DATE-YEAR": {
            "level": 60,
            "length": 2,
            "type": "numeric",
            "signed": false
          }
        },
        {
          "ACTION-DATE-MONTH": {
            "level": 40,
            "length": 2,
            "type": "numeric",
            "signed": false
          }
        },
        {
          "ACTION-DATE-DAY": {
            "level": 40,
            "length": 2,
            "type": "numeric",
            "signed": false
          }
        }
      ],
      "source": "sample/sample1.cpy"
    }

Convert copybook `sample`.cpy` to YAML and write to STDOUT:

    python copybook.py sample/sample1.cpy -yaml

Output:

```yaml
nodes:
- RECORD-01:
    level: 10
    type: record
  - RECORD-02:
      level: 20
      type: record
  - ACTION-DATE:
      level: 30
      type: record
  - ACTION-DATE-YEAR-CC:
      level: 40
      type: record
  - ACTION-DATE-CENT:
      level: 60
      length: 2
      type: numeric
      signed: false
  - ACTION-DATE-YEAR:
      level: 60
      length: 2
      type: numeric
      signed: false
  - ACTION-DATE-MONTH:
      level: 40
      length: 2
      type: numeric
      signed: false
  - ACTION-DATE-DAY:
      level: 40
      length: 2
      type: numeric
      signed: false
  source: sample/sample1.cpy
```

Convert copybook `sample`.cpy` to nested JSON and write to STDOUT:

    python copybook.py sample/sample1.cpy -nested

Output:

    {
      "Root": {
        "type": "record",
        "10": [
          {
            "RECORD-01": {
              "type": "record",
              "20": [
                {
                  "RECORD-02": {
                    "type": "record",
                    "30": [
                      {
                        "ACTION-DATE": {
                          "type": "record",
                          "40": [
                            {
                              "ACTION-DATE-YEAR-CC": {
                                "type": "record",
                                "60": [
                                  {
                                    "ACTION-DATE-CENT": {
                                      "length": 2,
                                      "type": "numeric",
                                      "signed": false
                                    }
                                  },
                                  {
                                    "ACTION-DATE-YEAR": {
                                      "length": 2,
                                      "type": "numeric",
                                      "signed": false
                                    }
                                  }
                                ]
                              }
                            },
                            {
                              "ACTION-DATE-MONTH": {
                                "length": 2,
                                "type": "numeric",
                                "signed": false
                              }
                            },
                            {
                              "ACTION-DATE-DAY": {
                                "length": 2,
                                "type": "numeric",
                                "signed": false
                              }
                            }
                          ]
                        }
                      }
                    ]
                  }
                }
              ]
            }
          }
        ]
      },
      "timestamp": "2024-07-22 15:33:24",
      "source": "sample/sample1.cpy"
    }

Convert copybook `sample`.cpy` to nested YAML and write to STDOUT:

    python copybook.py sample/sample1.cpy -yaml -nested

Output:

```yaml
Root:
  type: record
  '10':
  - RECORD-01:
      type: record
      '20':
      - RECORD-02:
          type: record
          '30':
          - ACTION-DATE:
              type: record
              '40':
              - ACTION-DATE-YEAR-CC:
                  type: record
                  '60':
                  - ACTION-DATE-CENT:
                      length: 2
                      type: numeric
                      signed: false
                  - ACTION-DATE-YEAR:
                      length: 2
                      type: numeric
                      signed: false
              - ACTION-DATE-MONTH:
                  length: 2
                  type: numeric
                  signed: false
              - ACTION-DATE-DAY:
                  length: 2
                  type: numeric
                  signed: false
timestamp: '2024-07-22 15:36:45'
source: sample/sample1.cpy
```

## Nested output notes

Nested output probably best represents the structure of the original copybook.
There are some limitations, though. Specifically, the algorithm will need to 
backtrack to the parent level when it finds a node with a lower level number
than the last node processed. This means that some rare copybook formats will
produce an error.

For example, this structure is permitted by COBOL, but will cause an exception
when converted:

    000001 10 RECORD-01.
    000002       30 ACTION-DATE.
    000003          40 ACTION-DATE-YEAR-CC.
    000004             60 ACTION-DATE-CENT             PIC 99.
    000005             60 ACTION-DATE-YEAR             PIC 99.
    000006          40 ACTION-DATE-MONTH               PIC 99.
    000007          40 ACTION-DATE-DAY                 PIC 99.
    000008    20 RECORD-02.
    000009       30 COMMISSION-RATE                    PIC V9(03).

The processor is unable to find a matching level-20 parent when it moves from
line 7 to line 8. This can be rectified by inserting a dummy level-20 record
just before the level-30 record.

    000001 10 RECORD-01.
    000002    20 DUMMY-LEVEL-20.
    000003       30 ACTION-DATE.
    000004          40 ACTION-DATE-YEAR-CC.
    000005             60 ACTION-DATE-CENT             PIC 99.
    000006             60 ACTION-DATE-YEAR             PIC 99.
    000007          40 ACTION-DATE-MONTH               PIC 99.
    000008          40 ACTION-DATE-DAY                 PIC 99.
    000009    20 RECORD-02.
    000010       30 COMMISSION-RATE                    PIC V9(03).