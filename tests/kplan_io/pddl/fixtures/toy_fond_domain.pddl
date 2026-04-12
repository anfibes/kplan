(define (domain toy-fond)
  (:requirements :typing :non-deterministic :negative-preconditions)
  (:predicates
    (at-start)
    (at-mid)
    (at-goal)
    (broken))

  (:action try
    :parameters ()
    :precondition (at-start)
    :effect (oneof
              (and (not (at-start)) (at-mid))
              (and (not (at-start)) (broken))))

  (:action finish
    :parameters ()
    :precondition (at-mid)
    :effect (and (not (at-mid)) (at-goal)))

  (:action reset
    :parameters ()
    :precondition (at-mid)
    :effect (and (not (at-mid)) (at-start))))
