(define (domain bad-when)
  (:requirements :typing :conditional-effects)
  (:predicates (a) (b))
  (:action act
    :parameters ()
    :precondition (a)
    :effect (when (a) (b))))
