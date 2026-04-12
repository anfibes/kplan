(define (domain det-toy)
  (:requirements :typing :negative-preconditions)
  (:types block)
  (:predicates
    (clear ?b - block)
    (holding ?b - block)
    (handempty))

  (:action pick
    :parameters (?b - block)
    :precondition (and (clear ?b) (handempty))
    :effect (and (not (clear ?b)) (not (handempty)) (holding ?b)))

  (:action put
    :parameters (?b - block)
    :precondition (holding ?b)
    :effect (and (not (holding ?b)) (clear ?b) (handempty))))
