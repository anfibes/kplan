(define (domain subtype-test)
  (:requirements :typing :negative-preconditions)
  (:types animal - object
          dog - animal
          cat - animal)
  (:predicates
    (friendly ?a - animal)
    (adopted ?a - animal))

  (:action adopt
    :parameters (?a - animal)
    :precondition (friendly ?a)
    :effect (and (adopted ?a) (not (friendly ?a)))))
