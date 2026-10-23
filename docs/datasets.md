# Datasets

Overview of the datasets supported by the converter.

TODO: Confirm values marked with `?`.

## Recording setup

| Dataset                                                                      | Location                                    | Road type                                     | Recording method           | Paper                                                                                                                                                                                                                                     |
| ---------------------------------------------------------------------------- | ------------------------------------------- | --------------------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [highD](https://www.highd-dataset.com/)                                      | Germany, 6 locations                        | Highway                                       | Drone                      | [Krajewski et al., ITSC 2018](https://arxiv.org/abs/1810.05642)                                                                                                                                                                           |
| [inD](https://www.ind-dataset.com/)                                          | Aachen, Germany, 4 locations                | Unsignalized urban intersections              | Drone                      | [Bock et al., IV 2020](https://arxiv.org/abs/1911.07602)                                                                                                                                                                                  |
| [rounD](https://www.round-dataset.com/)                                      | Germany, 3 locations                        | Roundabouts                                   | Drone                      | [Krajewski et al., ITSC 2020](https://doi.org/10.1109/ITSC45102.2020.9294728)                                                                                                                                                             |
| [exiD](https://www.exid-dataset.com/)                                        | Germany, 7 locations                        | Highway entries and exits                     | Drone                      | [Moers et al., IV 2022](https://www.ika.rwth-aachen.de/de/kompetenzen/publikationen/vortraege-artikel/fahrzeugintelligenz-automatisiertes-fahren/a-real-world-trajectory-dataset-of-highly-interactive-highway-scenarios-in-germany.html) |
| [uniD](https://levelxdata.com/unid-dataset/)                                 | RWTH Aachen University campus, Germany      | Shared space                                  | Drone                      |                                                                                                                                                                                                                                           |
| [INTERACTION](http://interaction-dataset.com/)                               | China, Germany, USA, Bulgaria?              | Merging, roundabouts, intersections           | Drones and traffic cameras | [Zhan et al., 2019](https://arxiv.org/abs/1910.03088)                                                                                                                                                                                     |
| [MONA](https://commonroad.in.tum.de/datasets)                                | Munich, Germany, 3 locations                | Urban multi-lane roads and inner-city highway | Stationary elevated camera | [Gressenbuch et al., ITSC 2022](https://mediatum.ub.tum.de/doc/1696182/document.pdf)                                                                                                                                                      |
| [SinD](https://github.com/SOTIF-AVLab/SinD)                                  | China: Tianjin, Changchun, Chongqing, Xi'an | Signalized intersections                      | Drone                      | [Xu et al., ITSC 2022](https://arxiv.org/abs/2209.02297)                                                                                                                                                                                  |
| [TUMDOT-MUC](https://www.mos.ed.tum.de/en/vt/research/data-sets/tumdot-muc/) | Munich, Germany, 700 m road section         | Inner-city road                               | 12 drones                  | [Kutsch et al., 2024](https://link.springer.com/article/10.1007/s42421-024-00101-5)                                                                                                                                                       |

## Size

| Dataset     | Recordings | Original sample time | Total time | Road users                  | Maps in converter       |
| ----------- | ---------- | -------------------- | ---------- | --------------------------- | ----------------------- |
| highD       | 60         | 0.04 s               | 16.5 h     | 110,000                     | Generated per recording |
| inD         | 33?        | 0.04 s               | 10 h       | 11,500                      | 4                       |
| rounD       | 23         | 0.04 s               | 6 h        | 13,746                      | 3                       |
| exiD        | 92         | 0.04 s               | 16 h?      | 69,172                      | 7                       |
| uniD        | 13?        | 0.04 s?              | 3 h?       | 1,124 vehicles, 7,101 VRUs? | 1                       |
| INTERACTION | ?          | 0.1 s?               | 16.5 h?    |                             | 12                      |
| MONA        | 298        | 0.04 s               | 133.8 h    | 718,000                     | 3                       |
| SinD        | ?          | 0.1 s                | 7 h?       | 13,000?                     | 4                       |
| TUMDOT-MUC  | ?          | 0.08 s               | ?          |                             | 1                       |

Notes:

- Road users include all types (cars, trucks, pedestrians, cyclists, …). The converter only converts cars.
- SinD figures refer to the Tianjin intersection from the original paper.
- TUMDOT-MUC is split into 10-minute files recorded on two weekdays.
