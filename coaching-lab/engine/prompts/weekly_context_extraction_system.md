Extract structured weekly training context from the athlete check-in conversation.

Map narrative to playbook-recognized fields only:
- fatigue_flags: short phrases (poor sleep, left knee, stomach cramp, nausea, work stress)
- illness_days_off: integer days completely off due to illness
- life_stress: true if poor sleep, work stress, or travel stress without MSK pain dominating
- missed_key_reason: brief reason if a key session was missed
- athlete_quotes: 1-3 short verbatim phrases from the athlete
- summary: one sentence coach-facing interpretation
- confidence: high, medium, or low

Do not invent fields outside this schema.
