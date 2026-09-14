# Extension round 1 report (2026-09-14T05:27:39Z)

Clips: 166; automatic valid 102, invalid 64

| polarity | class | valid | invalid |
|---|---|---|---|
| negative | decelerate | 2 | 7 |
| negative | maintain | 27 | 18 |
| negative | stop | 19 | 10 |
| positive | decelerate | 6 | 22 |
| positive | maintain | 24 | 5 |
| positive | stop | 24 | 2 |

Failure witnesses: ID trajectory disagrees 58, flow probe contradicts prompt 9

| clip | id | class | flow end | ID reasons | seeds tried |
|---|---|---|---|---|---|
| negative_scenarios/prompt_11.mp4 | 29 | maintain | unmeasurable | expected ~constant speed, end/start velocity=0.07 | [1234] |
| negative_scenarios/prompt_12.mp4 | 30 | stop | stopped | expected a stop, end_v=16.8 final=14.2 mph | [1234] |
| negative_scenarios/prompt_14.mp4 | 32 | maintain | unmeasurable | expected ~constant speed, end/start velocity=0.24 | [1234] |
| negative_scenarios/prompt_19.mp4 | 38 | maintain | unmeasurable | expected ~constant speed, end/start velocity=0.37 | [1234] |
| negative_scenarios/prompt_2.mp4 | 15 | maintain | moving | expected ~constant speed, end/start velocity=0.49 | [1234] |
| negative_scenarios/prompt_26.mp4 | 46 | maintain | unmeasurable | expected ~constant speed, end/start velocity=0.44 | [1234] |
| negative_scenarios/prompt_27.mp4 | 47 | maintain | moving | expected ~constant speed, end/start velocity=0.16 | [1234] |
| negative_scenarios/prompt_30.mp4 | 51 | stop | unmeasurable | expected a stop, end_v=9.3 final=5.9 mph | [1234] |
| negative_scenarios/prompt_33.mp4 | 54 | stop | moving | expected a stop, end_v=66.3 final=59.2 mph | [1234] |
| negative_scenarios/prompt_34.mp4 | 55 | decelerate | moving | expected deceleration, end/start velocity=11.59 | [1234] |
| negative_scenarios/prompt_35.mp4 | 57 | maintain | stopped |  | [1234] |
| negative_scenarios/prompt_36.mp4 | 59 | stop | unmeasurable | expected a stop, end_v=41.0 final=34.0 mph | [1234] |
| negative_scenarios/prompt_37.mp4 | 60 | stop | ambiguous | expected a stop, end_v=5.8 final=4.3 mph | [1234] |
| negative_scenarios/prompt_38.mp4 | 61 | decelerate | moving | expected deceleration, end/start velocity=1.00 | [1234] |
| negative_scenarios/prompt_39.mp4 | 62 | maintain | moving | expected ~constant speed, end/start velocity=0.47 | [1234] |
| negative_scenarios/prompt_42.mp4 | 66 | maintain | unmeasurable | expected ~constant speed, end/start velocity=0.01 | [1234] |
| negative_scenarios/prompt_44.mp4 | 68 | stop | stopped | expected a stop, end_v=52.7 final=38.3 mph | [1234] |
| negative_scenarios/prompt_45.mp4 | 69 | decelerate | moving | expected deceleration, end/start velocity=0.83 | [1234] |
| negative_scenarios/prompt_46.mp4 | 70 | maintain | unmeasurable | expected ~constant speed, end/start velocity=0.39 | [1234] |
| negative_scenarios/prompt_47.mp4 | 71 | maintain | unmeasurable | expected ~constant speed, end/start velocity=0.24 | [1234] |
| negative_scenarios/prompt_52.mp4 | 79 | maintain | unmeasurable | expected ~constant speed, end/start velocity=21.91 | [1234] |
| negative_scenarios/prompt_54.mp4 | 81 | stop | unmeasurable | expected a stop, end_v=2.3 final=2.0 mph | [1234] |
| negative_scenarios/prompt_58.mp4 | 85 | maintain | stopped |  | [1234] |
| negative_scenarios/prompt_6.mp4 | 23 | stop | ambiguous | expected a stop, end_v=52.0 final=43.2 mph | [1234] |
| negative_scenarios/prompt_60.mp4 | 87 | maintain | moving | expected ~constant speed, end/start velocity=83.63 | [1234] |
| negative_scenarios/prompt_66.mp4 | 93 | stop | unmeasurable | expected a stop, end_v=41.8 final=31.9 mph | [1234] |
| negative_scenarios/prompt_67.mp4 | 94 | maintain | unmeasurable | expected ~constant speed, end/start velocity=4.39 | [1234] |
| negative_scenarios/prompt_68.mp4 | 95 | maintain | moving | expected ~constant speed, end/start velocity=0.33 | [1234] |
| negative_scenarios/prompt_69.mp4 | 96 | decelerate | stopped |  | [1234] |
| negative_scenarios/prompt_71.mp4 | 98 | decelerate | unmeasurable | expected deceleration, end/start velocity=0.98 | [1234] |
| negative_scenarios/prompt_73.mp4 | 101 | stop | unmeasurable | expected a stop, end_v=11.6 final=9.2 mph | [1234] |
| negative_scenarios/prompt_78.mp4 | 107 | maintain | unmeasurable | expected ~constant speed, end/start velocity=0.27 | [1234] |
| negative_scenarios/prompt_79.mp4 | 108 | decelerate | moving | expected deceleration, end/start velocity=0.82 | [1234] |
| negative_scenarios/prompt_80.mp4 | 109 | maintain | ambiguous | expected ~constant speed, end/start velocity=0.42 | [1234] |
| negative_scenarios/prompt_9.mp4 | 27 | decelerate | unmeasurable | expected deceleration, end/start velocity=0.93 | [1234] |
| positive_scenarios/prompt_1.mp4 | 14 | decelerate | unmeasurable | expected deceleration, end/start velocity=0.92 | [1234] |
| positive_scenarios/prompt_12.mp4 | 30 | maintain | stopped |  | [1234] |
| positive_scenarios/prompt_20.mp4 | 39 | decelerate | unmeasurable | expected deceleration, end/start velocity=8.07 | [1234] |
| positive_scenarios/prompt_23.mp4 | 42 | decelerate | stopped | expected deceleration, end/start velocity=1.11 | [1234] |
| positive_scenarios/prompt_25.mp4 | 44 | decelerate | unmeasurable | expected deceleration, end/start velocity=4.88 | [1234] |
| positive_scenarios/prompt_26.mp4 | 46 | stop | ambiguous | expected a stop, end_v=2.2 final=3.5 mph | [1234] |
| positive_scenarios/prompt_28.mp4 | 49 | decelerate | unmeasurable | expected deceleration, end/start velocity=0.94 | [1234] |
| positive_scenarios/prompt_31.mp4 | 52 | decelerate | unmeasurable | expected deceleration, end/start velocity=0.92 | [1234] |
| positive_scenarios/prompt_33.mp4 | 54 | decelerate | unmeasurable | expected deceleration, end/start velocity=0.95 | [1234] |
| positive_scenarios/prompt_34.mp4 | 55 | maintain | unmeasurable | expected ~constant speed, end/start velocity=3.28 | [1234] |
| positive_scenarios/prompt_35.mp4 | 57 | decelerate | unmeasurable | expected deceleration, end/start velocity=0.76 | [1234] |
| positive_scenarios/prompt_4.mp4 | 19 | decelerate | moving | expected deceleration, end/start velocity=0.87 | [1234] |
| positive_scenarios/prompt_41.mp4 | 65 | decelerate | stopped | expected deceleration, end/start velocity=0.96 | [1234] |
| positive_scenarios/prompt_43.mp4 | 67 | maintain | stopped |  | [1234] |
| positive_scenarios/prompt_48.mp4 | 72 | decelerate | unmeasurable | expected deceleration, end/start velocity=1.25 | [1234] |
| positive_scenarios/prompt_49.mp4 | 73 | decelerate | unmeasurable | expected deceleration, end/start velocity=0.92 | [1234] |
| positive_scenarios/prompt_50.mp4 | 74 | decelerate | moving | expected deceleration, end/start velocity=0.92 | [1234] |
| positive_scenarios/prompt_53.mp4 | 80 | decelerate | unmeasurable | expected deceleration, end/start velocity=0.96 | [1234] |
| positive_scenarios/prompt_54.mp4 | 81 | decelerate | moving | expected deceleration, end/start velocity=0.76; expected steering, max|heading|=1.1deg | [1234] |
| positive_scenarios/prompt_58.mp4 | 85 | decelerate | ambiguous | expected deceleration, end/start velocity=0.90; expected steering, max|heading|=1.1deg | [1234] |
| positive_scenarios/prompt_60.mp4 | 87 | stop | unmeasurable | expected a stop, end_v=3.3 final=3.5 mph | [1234] |
| positive_scenarios/prompt_62.mp4 | 89 | decelerate | moving | expected deceleration, end/start velocity=105.48 | [1234] |
| positive_scenarios/prompt_63.mp4 | 90 | decelerate | unmeasurable | expected steering, max|heading|=3.5deg | [1234] |
| positive_scenarios/prompt_67.mp4 | 94 | decelerate | unmeasurable | expected deceleration, end/start velocity=40.11 | [1234] |
| positive_scenarios/prompt_69.mp4 | 96 | maintain | stopped |  | [1234] |
| positive_scenarios/prompt_77.mp4 | 106 | decelerate | moving | expected deceleration, end/start velocity=0.89 | [1234] |
| positive_scenarios/prompt_8.mp4 | 25 | maintain | unmeasurable | expected ~constant speed, end/start velocity=0.27 | [1234] |
| positive_scenarios/prompt_81.mp4 | 110 | decelerate | moving | expected deceleration, end/start velocity=2.02 | [1234] |
| positive_scenarios/prompt_82.mp4 | 111 | decelerate | moving | expected deceleration, end/start velocity=1.49 | [1234] |

Next round (4 seeds/clip, 64 clips): generation 61-154 min + ID ~17 min = $5.3-11.4 at $4.0/h (plus ~10 min instance setup).
