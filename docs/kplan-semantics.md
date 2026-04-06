k-plan Semantics

This document explains the meaning of k-plan in this project.

The goal is to describe the semantics in a precise and simple way.

⸻

1. Purpose

The kplan project studies planning in non-deterministic domains.

In these domains, one action may produce more than one possible result.

Example:
	•	a robot tries to move north
	•	the robot may move north
	•	or it may slip sideways
	•	or it may fail and stay in the same place

A planner must decide whether the goal can still be reached in this kind of environment.

The central question is:

How many adverse events can a plan tolerate while still guaranteeing the goal?

The answer is expressed by the k-plan value of a state.

⸻

2. Core idea

A k-plan is a plan or policy that guarantees the goal if the number of adverse outcomes does not exceed k.

This project uses an adversarial interpretation of non-determinism.

This means:
	•	the system does not assign probabilities to outcomes
	•	the system does not assume that the environment is friendly
	•	every possible outcome must be treated as a real possibility

The planner must therefore be correct in the worst case, not only in the average case.

⸻

3. Meaning of “adverse outcome”

When an action is executed, one result is usually considered the intended or favorable result.

Other possible results are considered adverse outcomes.

Example:
	•	intended action: move north
	•	intended result: reach the cell above
	•	adverse outcomes:
	•	slip left
	•	slip right
	•	remain in the current cell

In this model, adverse outcomes consume part of the available robustness budget.

⸻

4. Meaning of k

k is the maximum number of adverse outcomes that the plan can tolerate while still guaranteeing the goal.

Interpretation
	•	k = 0
A solution exists, but it tolerates zero adverse outcomes.
	•	k = 1
The solution tolerates one adverse outcome.
	•	k = 2
The solution tolerates two adverse outcomes.

And so on.

⸻

5. Meaning of kPlan(state)

For each reachable state, the solver computes an integer value called kPlan.

This value represents the maximum number of adverse outcomes that can be tolerated from that state while still guaranteeing the goal.

Informal definition

kPlan(s) = k means:

Starting from state s, there exists a policy that guarantees the goal if at most k adverse outcomes occur.

Important note

The value is attached to the state, not only to a single path.

This is important because the project is about policies, not just fixed action sequences.

A policy can choose different actions in different states.

⸻

6. Meaning of kPlan = -1

In the current implementation, -1 means:

No guarantee has been found for reaching the goal from this state.

This usually means one of the following:
	•	the goal is unreachable from that state
	•	the current robustness level cannot be guaranteed
	•	the state has not been promoted by the backward propagation process

In practice, -1 should be read as:

No valid k-plan is known for this state.

⸻

7. Meaning of kPlan = 0

This is a very important case.

kPlan = 0 means:

There exists a way to reach the goal, but the plan tolerates no adverse outcomes.

In other words:
	•	a successful strategy exists
	•	but if one adverse outcome happens, the guarantee is lost

This is the weakest non-negative guarantee.

It says:
	•	the state is solvable
	•	but not robust

⸻

8. Meaning of kPlan > 0

If kPlan(s) = i with i > 0, then the state is not only solvable, but also robust.

This means:

The policy can tolerate up to i adverse outcomes and still guarantee the goal.

Larger values mean stronger guarantees.

Example:
	•	kPlan = 0 → fragile solution
	•	kPlan = 1 → one failure tolerated
	•	kPlan = 2 → two failures tolerated

⸻

9. Why this is not a probabilistic planner

This project does not use probabilities in the core model.

It does not say:
	•	“this failure happens with 5% probability”
	•	“this action is better on average”
	•	“the expected utility is high”

Instead, it says:
	•	every listed outcome is possible
	•	the environment may behave in the worst possible way
	•	the plan must still work within the allowed number of adverse outcomes

This is why the model is called adversarial non-determinism.

⸻

10. Domain model

The planner works on a non-deterministic planning problem with:
	•	a set of states
	•	a set of actions
	•	one or more goal states
	•	a transition relation

An action does not produce one successor only.

It produces a set of possible successor states.

In code, this is represented by:
	•	initial_state()
	•	get_actions(state)
	•	get_successors(state, action)
	•	is_goal(state)

⸻

11. Reachable state space

The current solver first explores the reachable state space starting from the initial state.

During this phase, it builds:
	•	the set of reachable states
	•	the actions available in each state
	•	the set of successors of each (state, action) pair
	•	the set of predecessors of each state

This explicit representation is important because the current k-plan computation is based on backward propagation.

⸻

12. Backward propagation idea

The solver computes k-values by working backward from the goal states.

The intuition is:
	•	goal states are already solved
	•	if a state can safely move toward already solved states, then that state can also be solved
	•	this information is propagated backward through the graph

This process is repeated for increasing values of k.

⸻

13. Promotion rule

The current implementation uses the following idea.

A state can be promoted to robustness level i if there exists an action such that:
	•	all possible successors satisfy the minimum required guarantee for level i
	•	the propagation is reached from a successor already known to be valid at level i

Intuition

When the solver propagates backward from a valid state:
	•	the propagated branch acts as the favorable continuation
	•	the other possible outcomes must still remain safe enough

This corresponds to the idea that:
	•	the intended continuation does not consume robustness budget
	•	adverse outcomes consume one unit of robustness budget

⸻

14. Base case

At the beginning of the computation:
	•	all reachable states are initialized with kPlan = -1
	•	goal states are assigned the current level during propagation

This means:
	•	a goal state is always trivially valid for the requested level
	•	other states must be proved valid by backward propagation

This is why goal states always receive the highest requested level in the current run.

Example:
	•	if the solver is run with k = 3
	•	the goal state will end with kPlan = 3

This is intentional and correct.

If the system is already in a goal state, no further risk is required to satisfy the objective.

⸻

15. Monotonicity

A fundamental expected property is:

Increasing the allowed robustness budget should never make a state worse.

In other words, if a state is valid for k = 0, it should also remain valid when the solver is run with k = 1, k = 2, and so on.

This does not mean the state value stays unchanged.

It means that the computed robustness should be monotonic with respect to the allowed budget.

The current test suite already checks this property on simple cases.

⸻

16. Policy semantics

The solver returns both:
	•	a map of kPlan values
	•	a policy

The policy is a mapping:
	•	state -> action

For a non-goal state, the chosen action is the action that allowed promotion of that state during backward propagation.

For a goal state, the policy returns None, because no action is needed.

Important note

The current policy is explicit.

This means the solver stores a concrete action for each promoted state.

It is not yet an optimized or minimal policy. It is the first valid policy extracted from the propagation process.

⸻

17. Dead-ends

A state can be considered a dead-end if no valid k-plan can be found for it.

In the current implementation, such states remain at:

kPlan = -1

This does not necessarily mean the state is impossible to leave.

It means only that the solver has found no guaranteed way to reach the goal from that state under the current semantics.

⸻

18. Example intuition

Consider a rover on a grid.

The rover wants to reach a target cell.

Action: MOVE_NORTH

Possible outcomes:
	•	move north successfully
	•	slip left
	•	slip right
	•	stay in place

Now suppose:
	•	from the intended successor, the goal is still guaranteed at level i
	•	from the other successors, the goal is still guaranteed at level i - 1

Then the current state may be promoted to level i.

This is the operational meaning of robustness in this project.

⸻

19. Why state-based robustness matters

A simple path is not enough in a non-deterministic environment.

If the environment can change the result of an action, then a fixed sequence of actions may fail.

For this reason, the project reasons in terms of state-based policies.

This means:
	•	after each transition
	•	the controller can observe the new state
	•	and choose the next action based on that state

This is what makes the model robust.

⸻

20. Current limitations

The current implementation is intentionally simple.

It does not yet include:
	•	probabilistic outcomes
	•	partial observability
	•	action costs
	•	heuristic search
	•	compact symbolic representations
	•	large-scale optimization

The current goal is to provide a clear and correct foundation for bounded-failure robust planning.

⸻

21. Future extensions

Possible future directions include:
	•	richer example domains
	•	dead-end classification
	•	explicit distinction between favorable and adverse successors
	•	visualization of the explored graph and extracted policy
	•	probabilistic evaluation as a separate layer
	•	machine learning heuristics as optional support

These extensions should remain separate from the core semantics.

The core model should remain simple and explicit.

⸻

22. Summary

The semantics of kplan can be summarized as follows:
	•	the environment is non-deterministic
	•	non-determinism is interpreted adversarially
	•	each state receives a robustness value kPlan
	•	kPlan(s) is the maximum number of adverse outcomes tolerated from state s
	•	kPlan = 0 means solvable but not robust
	•	kPlan > 0 means increasingly robust
	•	kPlan = -1 means no guaranteed solution has been found
	•	the solver computes these values by backward propagation from goal states

This is the semantic foundation of the project.

⸻