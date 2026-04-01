# Status — Multiple Choice + Branching

- [x] Step 1: Create `difficult_dialogs/choices.py` — ChoiceOption, ChoiceSolverProtocol, parse_choice()
- [x] Step 2: Update `premises.py` — add choices, on_agree, on_disagree fields + file loading
- [ ] Step 3: Update `arguments.py` — list→dict premises, entry_point, next_premise() graph traversal
- [ ] Step 4: Update `policy.py` — _advance() via next_premise(), add MultiChoicePolicy
- [ ] Step 5: Update `builder.py` — choice(), on_agree(), on_disagree(), entry_point() fluent methods
- [ ] Step 6: Update `__init__.py` — export new symbols
- [ ] Step 7: Write tests — test_choices.py, test_branching.py, test_multichoice_policy.py, test_builder_choices.py
- [ ] Step 8: Update docs — argument-format.md, POLICIES.md, index.md, FAQ.md
