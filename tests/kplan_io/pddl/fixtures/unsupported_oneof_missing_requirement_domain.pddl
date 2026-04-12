(define (domain bad-oneof-missing-req)
  (:requirements :typing)
  (:predicates (a) (b) (start))

  (:action act
    :parameters ()
    :precondition (start)
    :effect (oneof (a) (b))))