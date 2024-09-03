# data_platform
This repo was originally intended for sharing coding between Argus data platform developers. As of Sept 1st, 2024 the repo is open for anyone to use. The code is made available under the Apache 2.0 licence.

Organization of code in this directory is as follows:
  
  tsdb_abstraction_layer (TAL): Contains implementation of the argus_tal package. This is the base Python package which abstracted read access from a TimeseriesDB. The current implementation of the argus_tal layer supports for the OpenTSDB 2.2 interface. 
  
  quilt: Holds implementation of the Quilt algorithm. The quilt layer runs on top of the TAL layer can be used to define temporal states.
  
  Example of quit app: https://github.com/argusiot/data_platform/blob/master/quilt_demos/first_extruder_states_applique.py
  
  Example of quilt state space definition: https://github.com/argusiot/data_platform/blob/master/quilt_demos/extruder_states_fine.json

  ai_stack_installer: Contains a bunch installer scripts to install the OpenTSDB+Grafana stack

  This full argus_tal & argus_quilt stack was deployed to monitor the machines in a cable and wire manufacturing plant for a year+.
  Later the argus_tal became the foundation for deploying an MLOps stack in a steel mill. The MLOps stack code has not been released as open source.
