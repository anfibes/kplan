(define (domain bad-init-type)
  (:requirements :typing)
  (:types fruit vehicle)
  (:predicates (ripe ?f - fruit))
  (:action eat
    :parameters (?f - fruit)
    :precondition (ripe ?f)
    :effect (not (ripe ?f))))
