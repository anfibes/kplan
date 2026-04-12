(define (domain bad-constants)
  (:requirements :typing)
  (:types block)
  (:constants c - block)
  (:predicates (clear ?b - block))
  (:action act
    :parameters ()
    :precondition (clear c)
    :effect (not (clear c))))
