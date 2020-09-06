# Funzler: a Functional Deficiency Diagnosis Tool
Funzler is a prototype tool for functional deficiency diagnosis. This is generated during the PhD work of the author.

## Dependencies
1. Required python libraries include numpy, pandas 0.24.0, pyyaml, xlrd >= 1.0.0.
1. Knowledge base should be available in the Causal Scenario Analysis (CSA). For the execution of a CSA, a [template](./csa/CSA_template_v1.1.xlsm) is provided. More detailed methodological aspects can be found in the dissertation.

## Usage in Terminal
1. Configure the knowledge base (from CSA) in [funzler.yaml](./config/funzler.yaml).
    - As an example of the CSA, [CSA_Example.xlsx](./csa/CSA_Example.xlsx) is provided. The CSA results have been generated during Experiment 2 of the dissertation.
1. Start and run a funzler session (a diagnosis job).
    - The script will inquire user for the observation of trigger-events. For each trigger-event, a value from {1, -1, 0} should be given, respectively representing {"present", "absent", "unknown"};
    - For example, for a 5-events-observation, an user input 1 1 1 1 -1 means the 5th trigger-event is absent and others are present.

    ```
    python3 funzler_start.py
    ```
1. If the previous script outputs a label "fail pending" and some measurement updates are possible, e.g. via human annotation, update and rerun the funzler session (diagnosis job).
    - The script will inquire user for the updated boundary states, which are seperated by spaces
    - For example, 1 1 23 1 34 0 means the boundary id 1 is updated as present (or intensity index equal 1.0), the boundary id 23 as present, and the boundary id 34 as absent.
    ```
    python3 funzler_update.py
    ```

## Usage in Jupyter Notebook
```
jupyter notebook funzler.ipynb
```

