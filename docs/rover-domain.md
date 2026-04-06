Rover Domain

This document describes the Rover Gridworld domain used as the first example in the kplan project.

The rover domain is intentionally simple, but it already captures the key challenges of non-deterministic planning.

⸻

1. Purpose

The rover domain is used to:
	•	demonstrate how to define a planning problem
	•	illustrate non-deterministic transitions
	•	validate the k-plan semantics
	•	provide a minimal working example of the system

It is not intended to be realistic.
It is designed to be clear, small, and predictable.

⸻

2. Environment

The environment is a 2D grid defined by:
	•	width
	•	height

Each cell is identified by integer coordinates:

(x, y)

Coordinate system
	•	x increases to the right
	•	y increases upward

Example:

(0,1)  (1,1)
(0,0)  (1,0)


⸻

3. State representation

The rover state is defined as:

RoverState(x: int, y: int)

Properties:
	•	immutable
	•	hashable
	•	uniquely identifies a grid position

The state does not include:
	•	orientation
	•	velocity
	•	energy

These may be added in future extensions.

⸻

4. Actions

The rover has four actions:
	•	MOVE_NORTH
	•	MOVE_SOUTH
	•	MOVE_EAST
	•	MOVE_WEST

Actions are always available (no preconditions).

⸻

5. Non-deterministic transitions

Each action produces multiple possible outcomes.

Example: MOVE_NORTH

Possible results:
	•	move north (x, y + 1) → intended outcome
	•	slip left (x - 1, y)
	•	slip right (x + 1, y)
	•	stay in place (x, y)

This pattern is applied to all directions.

⸻

6. Interpretation of outcomes

For each action:
	•	one outcome is the intended result
	•	all others are adverse outcomes

The planner must consider all of them.

This is essential for k-plan semantics.

⸻

7. Boundaries

The grid has hard boundaries.

If a transition leads outside the grid:
	•	the rover remains in the current state

Example:

state = (0,0)
action = MOVE_WEST

result → (0,0)

This models failed movement.

⸻

8. Obstacles

The domain supports blocked cells:

blocked_cells: FrozenSet[(x, y)]

Rules:
	•	the rover cannot enter a blocked cell
	•	if a transition leads to a blocked cell:
	•	the rover remains in the current state

Example:

target cell is blocked → stay in place


⸻

9. Validity constraints

The domain enforces the following rules:
	•	grid size must be positive
	•	initial state must be inside the grid
	•	goal state must be inside the grid
	•	initial state cannot be blocked
	•	goal state cannot be blocked
	•	blocked cells must be inside the grid

These checks are performed at initialization.

⸻

10. Goal condition

The goal is defined as:

state == goal

There is a single goal state.

The solver treats goal states as:
	•	already solved
	•	maximally robust for the requested k

⸻

11. Deterministic vs non-deterministic behavior

This domain is intentionally non-deterministic.

Even if an action is chosen:
	•	the result is not guaranteed
	•	multiple outcomes must be considered

This is what makes the domain suitable for testing k-plan.

⸻

12. Example

Consider a 2x2 grid:

(0,1)  (1,1)  ← goal
(0,0)  (1,0)

Initial state:

(0,0)

Goal:

(1,1)

From (0,0):
	•	moving north may:
	•	reach (0,1)
	•	slip to (1,0)
	•	stay in (0,0)

The planner must find a policy that handles all these possibilities.

⸻

13. Why this domain is useful

This domain is small but expressive.

It allows us to test:
	•	non-deterministic transitions
	•	robustness propagation
	•	unreachable goals
	•	effect of obstacles
	•	monotonicity of k-values

It is ideal for:
	•	debugging
	•	testing
	•	explaining the algorithm

⸻

14. Limitations

The rover domain is intentionally minimal.

It does not include:
	•	orientation
	•	costs
	•	time
	•	energy constraints
	•	stochastic models

These can be added later.

⸻

15. Possible extensions

Future versions may include:
	•	directional movement with orientation
	•	energy consumption
	•	dynamic obstacles
	•	probabilistic transitions
	•	partial observability

These extensions should remain compatible with the core model.

⸻

16. Summary

The rover domain provides:
	•	a simple grid environment
	•	explicit non-deterministic transitions
	•	clear interpretation of adverse outcomes
	•	a clean testbed for k-plan algorithms

It is the reference domain for the current implementation.
:::

⸻