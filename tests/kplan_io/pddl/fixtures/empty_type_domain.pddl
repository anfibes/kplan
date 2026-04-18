(define (domain empty-type)
  (:requirements :typing)
  (:types tool weapon)
  (:predicates (sharp ?w - weapon) (useful ?t - tool))
  (:action sharpen
    :parameters (?w - weapon)
    :precondition (sharp ?w)
    :effect (not (sharp ?w)))
  (:action use
    :parameters (?t - tool)
    :precondition (useful ?t)
    :effect (not (useful ?t))))
