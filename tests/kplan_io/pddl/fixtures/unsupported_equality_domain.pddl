(define (domain bad-equality)
  (:requirements :typing :equality)
  (:types t)
  (:predicates (p ?x - t))
  (:action act
    :parameters (?x - t ?y - t)
    :precondition (= ?x ?y)
    :effect (p ?x)))
