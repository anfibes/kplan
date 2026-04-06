Architecture

This document describes the architecture of the kplan project.

The goal is to explain how the system is structured, how components interact, and how responsibilities are separated.

⸻

1. Design goals

The architecture is designed with the following goals:
	•	Clarity: each component has a clear responsibility
	•	Modularity: domains, algorithms, and core abstractions are separated
	•	Extensibility: new domains and algorithms can be added without changing existing code
	•	Testability: each layer can be tested independently
	•	Simplicity: avoid unnecessary complexity in the core model

⸻

2. High-level overview

The project is organized into five main layers:
    1. Core abstractions
    2. Algorithms
    3. Domains
    4. Visualization
    5. Tests and documentation

core/           → generic abstractions
algorithms/     → planning algorithms
domains/        → concrete problem definitions
visualization/  → graph rendering (Graphviz)
scripts/        → runnable examples
outputs/        → generated artifacts
tests/          → validation
docs/           → documentation

Each layer depends only on the layers below it.

⸻

3. Core layer

The core module defines the fundamental abstractions used by the system.

It does not depend on any specific domain or algorithm.

Key components

State
Represents a configuration of the world.
	•	immutable
	•	hashable
	•	used as key in dictionaries and sets

Action
Represents an operation that can be applied to a state.

Actions are domain-specific, but the concept is abstracted in the core.

Problem
Defines a planning problem.

initial_state()
get_actions(state)
get_successors(state, action)
is_goal(state)

This interface is the contract between domains and algorithms.

Policy
Defines how actions are selected.

get_action(state) -> Optional[Action]

A policy maps states to actions.

Planner
Defines the interface for planning algorithms.

solve(problem, k) -> PlanningResult

PlanningResult
Encapsulates the output of the solver:
	•	k_values: mapping from state to robustness level
	•	policy: mapping from state to action

⸻

4. Algorithms layer

The algorithms module contains concrete implementations of planning algorithms.

Current implementation

KPlanSolver
The main solver of the project.

Responsibilities:
	•	explore the reachable state space
	•	build explicit graph structures:
	•	states
	•	successors
	•	predecessors
	•	compute kPlan values using backward propagation
	•	extract a policy

Internal data structures

The solver maintains:
	•	states: set of reachable states
	•	actions_by_state: available actions per state
	•	successors_by_state_action: transition relation
	•	predecessors_by_state: reverse transition relation
	•	k_values: robustness values
	•	policy_actions: selected action per state

Execution flow
	1.	Explore reachable states
	2.	Build graph (successors and predecessors)
	3.	Initialize k-values
	4.	Propagate values backward from goals
	5.	Extract policy

⸻

5. Domains layer

The domains module contains concrete problem definitions.

Each domain implements the Problem interface.

Example: Rover domain

Located in:

domains/rover/

Components:
	•	state.py → defines RoverState
	•	actions.py → defines RoverAction
	•	problem.py → defines RoverProblem

Responsibilities:
	•	define the state representation
	•	define available actions
	•	define transition rules (including non-determinism)
	•	define goal conditions

Domain isolation

Domains do not depend on algorithms.

This allows:
	•	reuse of the same domain with different solvers
	•	easy addition of new domains

⸻

6. Visualization layer

The visualization module provides tools to inspect and understand the planning process.

Located in:

visualization/

Main components

GraphvizExporter

The GraphvizExporter is responsible for rendering the graph in a domain-agnostic way.

Responsibilities:
    • generate DOT representations of the explored graph
    • render nodes and edges using generic rules
    • support multiple rendering modes:
        • full_graph → entire state space
        • policy_only → only states reachable under the policy

The exporter does not contain any domain-specific logic.
All domain-specific behavior is delegated to VisualizationProfile.

⸻

VisualizationProfile

Domain-specific visualization logic is delegated to VisualizationProfile.

Each domain can define its own profile by extending:

VisualizationProfile[State, Action]

Responsibilities:
    • define how states are represented (state_repr)
    • define sorting rules (state_sort_key)
    • define clustering logic (cluster_key, cluster_label)
    • define semantic styling (e.g. bad outcomes)
    • define graph metadata:
        • title
        • explanation
        • state format

Example:

visualization/profiles/omelette_profile.py

⸻

Separation of concerns

Visualization is split into:
    • GraphvizExporter → generic rendering engine
    • VisualizationProfile → domain-specific behavior

This ensures:
    • no domain logic inside the renderer
    • easy addition of new domains
    • consistent rendering across different problems

⸻

7. Data flow

The interaction between components follows this flow:

Problem → Solver → PlanningResult → Visualization

PlanningResult contains:
    • k_values
    • policy

Step-by-step
	1.	The domain defines a Problem
	2.	The solver explores the state space
	3.	The solver computes k_values
	4.	The solver extracts a Policy
	5.	The result is returned as a PlanningResult
	6.  The result can be visualized through the visualization module

⸻

8. Non-determinism handling

The system models non-determinism explicitly.

Each action returns a set of successor states:

get_successors(state, action) -> Set[State]

This is central to the design:
	•	the solver must consider all possible outcomes
	•	no probability is assigned to outcomes
	•	all outcomes are treated as possible

⸻

9. Backward propagation model

The solver uses a backward propagation strategy:
	•	start from goal states
	•	propagate information to predecessors
	•	assign increasing robustness levels

This requires explicit access to:
	•	successors (forward edges)
	•	predecessors (reverse edges)

This is why both structures are stored.

⸻

10. Separation of concerns

The architecture enforces clear boundaries:

Core
	•	defines interfaces
	•	contains no domain logic
	•	contains no algorithm logic

Algorithms
	•	implement logic using the core interfaces
	•	do not depend on specific domains

Domains
	•	implement specific problems
	•	do not depend on algorithms

This separation ensures that:
	•	algorithms can be reused across domains
	•	domains can be tested independently
	•	new solvers can be added easily

⸻

11. Policy representation

The current implementation uses an explicit policy:

state -> action

Characteristics:
	•	simple
	•	deterministic
	•	directly derived from propagation

Limitations:
	•	not optimized
	•	may not be minimal
	•	does not handle tie-breaking strategies

Future versions may introduce:
	•	lazy policies
	•	symbolic policies
	•	cost-aware policies

⸻

12. Testing strategy

The project uses multiple levels of testing:

Domain tests

Validate:
	•	state transitions
	•	boundary conditions
	•	invalid configurations

Solver structural tests

Validate:
	•	exploration
	•	graph construction
	•	successors and predecessors

Semantic tests

Validate:
	•	meaning of kPlan
	•	monotonicity
	•	unreachable states
	•	policy existence

This layered testing approach ensures correctness at different levels.

⸻

13. Extensibility

The architecture allows extension in multiple directions.

New domains

To add a new domain:
	•	define a new state class
	•	define actions
	•	implement Problem

No change to the solver is required.

New algorithms

To add a new solver:
	•	implement the Planner interface
	•	reuse existing domains

Additional layers

Future additions may include:
    • probabilistic evaluation layer
    • heuristic search components
    • advanced visualization features

Visualization support

To add visualization for a new domain:
    • implement a VisualizationProfile
    • pass it to GraphvizExporter

No change to the exporter is required.

⸻

14. Visualization extension example

The visualization layer is designed to remain generic.

When a new domain requires domain-specific graph rendering, the recommended approach is:

    • keep GraphvizExporter generic
    • define a domain-specific VisualizationProfile
    • pass that profile to the exporter from the domain script

This avoids mixing domain logic inside the renderer.

Typical customization points include:

    • how states are represented
    • how states are sorted
    • how nodes are grouped into clusters
    • how adverse outcomes are recognized
    • how graph metadata is generated

Example workflow

1. Create a domain-specific profile

Example:

visualization/profiles/omelette_profile.py

This profile can define:

    • graph_title(...)
    • graph_explanation(...)
    • graph_state_format(...)
    • state_repr(...)
    • state_sort_key(...)
    • is_bad_outcome(...)
    • cluster_key(...)
    • cluster_label(...)

2. Keep the exporter generic

GraphvizExporter should not know anything about:
    • eggs
    • grid cells
    • energy
    • electrical loads
    • photovoltaic production

It should only ask the profile how the domain should be rendered.

3. Use the profile in the runnable script

Example:

profile = OmeletteVisualizationProfile()

exporter = GraphvizExporter(
    mode="policy_only",
    profile=profile,
    requested_k=2,
)

This makes the rendering configurable without changing the exporter itself.

Guideline for future domains

When adding a new domain, ask:

    • Do we need a custom state label?
    • Do we need domain-specific clustering?
    • Do we need to highlight specific semantic cases?
    • Do we need custom graph metadata?

If the answer is yes, create a new VisualizationProfile.

If the answer is no, the default VisualizationProfile is enough.

Examples of future profiles

Possible future profiles may include:

    • RoverVisualizationProfile
    • PowerGridVisualizationProfile
    • PhotovoltaicIntegrationVisualizationProfile

Each profile should contain only rendering semantics for its domain.

The planning semantics must remain in:
    • core/
    • algorithms/
    • domains/

not in the visualization layer.

⸻

Minimal profile skeleton

```python
from visualization.profile import VisualizationProfile

class MyDomainVisualizationProfile(VisualizationProfile[MyState, MyAction]):
    def state_repr(self, state: MyState) -> str:
        return str(state)

    def state_sort_key(self, state: MyState):
    	return (str(state),)

    def is_bad_outcome(self, state: MyState) -> bool:
        return False
```
⸻

15. Current limitations

The current architecture is intentionally simple.

It does not yet include:
	•	symbolic representations (BDD, SAT, etc.)
	•	large-scale optimizations
	•	memory-efficient graph structures
	•	parallel execution
	•	partial observability

These can be added later without breaking the core design.

⸻

16. Summary

The architecture of kplan is based on:
	•	clear separation between abstractions, algorithms, and domains
	•	explicit representation of non-deterministic transitions
	•	backward propagation of robustness values
	•	simple and testable components
	• 	a decoupled visualization layer using profiles for domain-specific rendering

This provides a solid foundation for further development and experimentation.

⸻