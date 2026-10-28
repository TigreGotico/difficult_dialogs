# Sample Argument Graphs

Premise graphs for all [sample arguments](../examples/sample_arguments/),
generated with `did graph`. Each node is a premise; edges show the dialog
flow (agree/disagree/choice). Mermaid diagrams render natively on GitHub.

> **Regenerate:** `for d in examples/sample_arguments/*/*; do did graph "$d"; done`

---

## Education

### critical thinking should be taught in schools
*2 premises, 10 statements*

```mermaid
graph TD
    enhances_problem_solving_skills["enhances_problem_solving_skills\n(5 stmts)"]
    promotes_independent_learning["promotes_independent_learning\n(5 stmts)"]
    enhances_problem_solving_skills --> promotes_independent_learning
```

### lifelong learning is essential in modern society
*2 premises, 10 statements*

```mermaid
graph TD
    professional_development_and_adaptability["professional_development_and_adaptability\n(5 stmts)"]
    personal_growth_and_self_improvement["personal_growth_and_self_improvement\n(5 stmts)"]
    professional_development_and_adaptability --> personal_growth_and_self_improvement
```

### online learning is as effective as in-person
*2 premises, 10 statements*

```mermaid
graph TD
    accessibility_and_reach["accessibility_and_reach\n(5 stmts)"]
    academic_performance["academic_performance\n(5 stmts)"]
    accessibility_and_reach --> academic_performance
```

### standardized tests dont measure intelligence
*2 premises, 11 statements*

```mermaid
graph TD
    standardized_tests_focus_on_narrow_skills["standardized_tests_focus_on_narrow_skills\n(5 stmts)"]
    standardized_tests_do_not_account_for_cognitive_diversity["standardized_tests_do_not_account_for_cognitive_diversity\n(6 stmts)"]
    standardized_tests_focus_on_narrow_skills --> standardized_tests_do_not_account_for_cognitive_diversity
```

### teachers should be paid more
*2 premises, 10 statements*

```mermaid
graph TD
    teacher_salary_disparity["teacher_salary_disparity\n(5 stmts)"]
    impact_of_salary_on_retention["impact_of_salary_on_retention\n(5 stmts)"]
    teacher_salary_disparity --> impact_of_salary_on_retention
```

## Health

### a plant-based diet is healthier
*2 premises, 10 statements*

```mermaid
graph TD
    reduced_risk_of_chronic_diseases["reduced_risk_of_chronic_diseases\n(5 stmts)"]
    nutrient_dense_and_balanced["nutrient_dense_and_balanced\n(5 stmts)"]
    reduced_risk_of_chronic_diseases --> nutrient_dense_and_balanced
```

### meditation reduces stress effectively
*2 premises, 10 statements*

```mermaid
graph TD
    physiological_effects["physiological_effects\n(5 stmts)"]
    psychological_benefits["psychological_benefits\n(5 stmts)"]
    physiological_effects --> psychological_benefits
```

### preventive care is better than treatment
*2 premises, 10 statements*

```mermaid
graph TD
    improved_health_outcomes_from_prevention["improved_health_outcomes_from_prevention\n(5 stmts)"]
    cost_effectiveness_of_preventive_care["cost_effectiveness_of_preventive_care\n(5 stmts)"]
    improved_health_outcomes_from_prevention --> cost_effectiveness_of_preventive_care
```

### regular exercise improves mental health
*2 premises, 14 statements*

```mermaid
graph TD
    lowers_stress_levels["lowers_stress_levels\n(7 stmts)"]
    reduces_symptoms_of_depression["reduces_symptoms_of_depression\n(7 stmts)"]
    lowers_stress_levels --> reduces_symptoms_of_depression
```

### sleep is essential for cognitive function
*2 premises, 12 statements*

```mermaid
graph TD
    attention_and_cognitive_performance["attention_and_cognitive_performance\n(6 stmts)"]
    memory_consolidation["memory_consolidation\n(6 stmts)"]
    attention_and_cognitive_performance --> memory_consolidation
```

## Philosophy

### free will exists
*2 premises, 14 statements*

```mermaid
graph TD
    moral_responsibility["moral_responsibility\n(7 stmts)"]
    human_decision_making["human_decision_making\n(7 stmts)"]
    moral_responsibility --> human_decision_making
```

### happiness is the highest good
*2 premises, 10 statements*

```mermaid
graph TD
    happiness_is_intrinsic_value["happiness_is_intrinsic_value\n(5 stmts)"]
    happiness_drives_human_progress["happiness_drives_human_progress\n(5 stmts)"]
    happiness_is_intrinsic_value --> happiness_drives_human_progress
```

### i think therefore i am
*2 premises, 14 statements*

```mermaid
graph TD
    existence_through_thought["existence_through_thought\n(7 stmts)"]
    self_awareness_and_certainty["self_awareness_and_certainty\n(7 stmts)"]
    existence_through_thought --> self_awareness_and_certainty
```

### knowledge is more valuable than pleasure
*2 premises, 10 statements*

```mermaid
graph TD
    knowledge_drives_progress["knowledge_drives_progress\n(5 stmts)"]
    knowledge_enables_growth["knowledge_enables_growth\n(5 stmts)"]
    knowledge_drives_progress --> knowledge_enables_growth
```

### the ends justify the means
*2 premises, 10 statements*

```mermaid
graph TD
    ethical_integrity_matters["ethical_integrity_matters\n(5 stmts)"]
    means_influence_ends["means_influence_ends\n(5 stmts)"]
    ethical_integrity_matters --> means_influence_ends
```

## Science

### climate change requires immediate action
*2 premises, 12 statements*

```mermaid
graph TD
    scientific_consensus["scientific_consensus\n(6 stmts)"]
    economic_and_social_impact["economic_and_social_impact\n(6 stmts)"]
    scientific_consensus --> economic_and_social_impact
```

### genetic engineering should be regulated
*2 premises, 10 statements*

```mermaid
graph TD
    ethical_and_social_implications["ethical_and_social_implications\n(5 stmts)"]
    risk_of_unintended_consequences["risk_of_unintended_consequences\n(5 stmts)"]
    ethical_and_social_implications --> risk_of_unintended_consequences
```

### renewable energy can replace fossil fuels
*2 premises, 12 statements*

```mermaid
graph TD
    renewable_energy_sustainability["renewable_energy_sustainability\n(6 stmts)"]
    renewable_energy_economic_growth["renewable_energy_economic_growth\n(6 stmts)"]
    renewable_energy_sustainability --> renewable_energy_economic_growth
```

### space exploration is worth the cost
*2 premises, 11 statements*

```mermaid
graph TD
    economic_growth["economic_growth\n(5 stmts)"]
    scientific_advancements["scientific_advancements\n(6 stmts)"]
    economic_growth --> scientific_advancements
```

### vaccines are safe and effective
*2 premises, 14 statements*

```mermaid
graph TD
    vaccines_are_safe["vaccines_are_safe\n(7 stmts)"]
    vaccines_are_effective["vaccines_are_effective\n(7 stmts)"]
    vaccines_are_safe --> vaccines_are_effective
```

## Society

### cities should prioritize public transportation
*2 premises, 12 statements*

```mermaid
graph TD
    economic_and_social_benefits["economic_and_social_benefits\n(6 stmts)"]
    reduces_traffic_and_pollution["reduces_traffic_and_pollution\n(6 stmts)"]
    economic_and_social_benefits --> reduces_traffic_and_pollution
```

### higher education should be free
*2 premises, 12 statements*

```mermaid
graph TD
    social_mobility["social_mobility\n(6 stmts)"]
    economic_growth["economic_growth\n(6 stmts)"]
    social_mobility --> economic_growth
```

### recycling programs are effective
*2 premises, 12 statements*

```mermaid
graph TD
    conserves_natural_resources["conserves_natural_resources\n(6 stmts)"]
    reduces_waste_volume["reduces_waste_volume\n(6 stmts)"]
    conserves_natural_resources --> reduces_waste_volume
```

### universal basic income would reduce poverty
*2 premises, 12 statements*

```mermaid
graph TD
    financial_security_for_all["financial_security_for_all\n(6 stmts)"]
    economic_participation_and_growth["economic_participation_and_growth\n(6 stmts)"]
    financial_security_for_all --> economic_participation_and_growth
```

### volunteering benefits both giver and receiver
*2 premises, 10 statements*

```mermaid
graph TD
    personal_growth_and_skill_development["personal_growth_and_skill_development\n(5 stmts)"]
    community_and_social_impact["community_and_social_impact\n(5 stmts)"]
    personal_growth_and_skill_development --> community_and_social_impact
```

## Technology

### artificial intelligence will benefit humanity
*2 premises, 12 statements*

```mermaid
graph TD
    economic_growth["economic_growth\n(6 stmts)"]
    healthcare_improvements["healthcare_improvements\n(6 stmts)"]
    economic_growth --> healthcare_improvements
```

### open source software is superior to proprietary
*2 premises, 10 statements*

```mermaid
graph TD
    cost_and_accessibility["cost_and_accessibility\n(5 stmts)"]
    transparency_and_security["transparency_and_security\n(5 stmts)"]
    cost_and_accessibility --> transparency_and_security
```

### privacy is more important than convenience
*2 premises, 10 statements*

```mermaid
graph TD
    convenience_compromises_long_term_security["convenience_compromises_long_term_security\n(5 stmts)"]
    privacy_protection_individual_rights["privacy_protection_individual_rights\n(5 stmts)"]
    convenience_compromises_long_term_security --> privacy_protection_individual_rights
```

### remote work increases productivity
*2 premises, 12 statements*

```mermaid
graph TD
    fewer_workplace_distractions_increase_focus["fewer_workplace_distractions_increase_focus\n(6 stmts)"]
    work_life_balance_improves_productivity["work_life_balance_improves_productivity\n(6 stmts)"]
    fewer_workplace_distractions_increase_focus --> work_life_balance_improves_productivity
```

### should ai be regulated *(branching)*
*5 premises, 10 statements*

```mermaid
graph TD
    implementation["implementation\n(2 stmts)"]
    oversight{"oversight\n(2 stmts)"}
    innovation["innovation\n(2 stmts)"]
    balance["balance\n(2 stmts)"]
    ai_risk["ai_risk\n(2 stmts)"]
    oversight -->|"choice:A"| implementation
    oversight -->|"choice:B"| balance
    innovation -->|"agree"| balance
    innovation -->|"disagree"| oversight
    ai_risk -->|"agree"| oversight
    ai_risk -->|"disagree"| innovation
```

### social media does more harm than good
*2 premises, 6 statements*

```mermaid
graph TD
    erosion_of_truth["erosion_of_truth\n(3 stmts)"]
    mental_health_harm["mental_health_harm\n(3 stmts)"]
    erosion_of_truth --> mental_health_harm
```

---
[← CLI](cli.md) · [Home](index.md) · [User guide →](USER_GUIDE.md)
