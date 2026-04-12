(define (domain fond-and-oneof)
  (:requirements :typing :non-deterministic :negative-preconditions)
  (:types block)
  (:predicates
    (clear ?b - block)
    (holding ?b - block)
    (handempty)
    (slipped))

  (:action grab
    :parameters (?b - block)
    :precondition (and (clear ?b) (handempty))
    :effect (and
              (not (clear ?b))
              (not (handempty))
              (oneof
                (holding ?b)
                (slipped)))))
