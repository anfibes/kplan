(define (domain conflict-add-del)
  (:requirements :typing :non-deterministic :negative-preconditions)
  (:predicates (a) (b))
  (:action act
    :parameters ()
    :precondition (a)
    :effect (and
              (not (a))
              (oneof (a) (b)))))
