(define (domain bad-or)
  (:requirements :typing :disjunctive-preconditions)
  (:predicates (a) (b) (c))
  (:action act
    :parameters ()
    :precondition (or (a) (b))
    :effect (c)))
