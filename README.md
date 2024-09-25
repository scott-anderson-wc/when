# when

A project to facilitate group work among people

## About
This is a project about 

* collecting availability data from students in a course or group, using an interface very much like [whenisgood.net](https://whenisgood.net/)
* computing *good* matches (pairs) or larger groups where "good" is defined as a sufficient overlap of available time, so that they can work together, and
* displaying the matches in a useful way

## Definitions and Representation

A student's schedule is represented as 7 sets of time slots, one for each day of the week, and 
the sets are half-hour time slots from 9am to 12midnight. That's 15 hours or 30 half-hour slots.

A "matching" is a list of pairs (i,j) where student i is matched with student j such that every student has a match.

Murphy's law says that if we want pairs, there will be an odd number of students in the class. We don't yet deal with that.

My current definition of a "good" matching is:

1. the number of overlapping time slots in a day
2. minus the number of such overlaps

Example 1:

On Saturday, Alice is available from 10am-2pm and Betty is available from 10:30am to 1:00pm. They overlap from 10:30-1:30 which is 5 slots. There's one such overlap, so 5-1 is a day_score of 4.

Example 2:

On Saturday, Cathy is available from 10am-11am and 12pm-1pm and 2pm-3pm and 4pm-5pm. Debby is available from 10:30am-11:30am, 12:30pm-1:30pm, 2:30pm-3:30pm and 4:30pm-5:30pm. They overlap from 10-10:30, from 11-11:30, from 12-12:. I need to work on this example more, and add a picture.

The above is the `day_score`.

The "overlap" between two students is the sum of their `day_score` values. 

The goodness of a matching is the sum of the overlaps, plus the *minimum* overlap, again, to boost its importance. But I think we need to do better.


## To Do

* Understand the current code
* improve the cleanliness and modularity of the code
    * proper classes and object-oriented programming
    * flexible and transparent choice of algorithm
* new definitions of "good" matchings
* algorithms for finding good matchings
* algorithms for finding several good matchings, without repeats
* algorithms for creating larger groups, say groups of 3 or 4 students instead of 2
* 
