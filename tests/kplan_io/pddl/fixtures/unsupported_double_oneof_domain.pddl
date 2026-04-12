(define (domain bad-double-oneof)
  (:requirements :typing :non-deterministic)
  (:predicates (a) (b) (c) (d) (start))
  (:action act
    :parameters ()
    :precondition (start)
    :effect (and
              (oneof (a) (b))
              (oneof (c) (d)))))
