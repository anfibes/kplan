(define (domain bad-action-type)
  (:requirements :typing :negative-preconditions)
  (:types fruit vehicle)
  (:predicates (ripe ?f - fruit) (parked ?v - vehicle))

  (:action drive
    :parameters (?v - vehicle)
    :precondition (parked ?v)
    :effect (and (not (parked ?v)) (ripe ?v))))
