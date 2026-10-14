When pointing the user at a pipeline command (hand-off lines like "next step: run …"), always use the namespaced form `/aia:<name>` (e.g. `/aia:product`, `/aia:plan`), never the bare `/plan`: consumer projects only install `/aia:*`.
This is for user-facing prose only; invoke skills with the `Skill` tool by bare name (`Skill(skill="plan")`), and skills refer to each other by bare name.
