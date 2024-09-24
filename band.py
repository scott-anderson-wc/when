'''Objects of this class represent a set of people, each of whom has a
schedule. There are lots of terms for a collective of people, such as
Class (but that's a reserved word in Python), Herd (too bovine), Gang
(too thuggish), party (too festive), etc.  I decided to go with
'band'.

In our usage, a band will typically comprise the enrollment roster of a
college course, where we want them to be able to work together.

Actually, "roster" is a pretty good word, too.

'''

# Days of the week are numbered starting at zero for Sunday, abbreviate to 3 letters

number_to_day = 'sun,mon,tue,wed,thu,fri,sat'.split(',')

# Dictionary mapping day names to their index

day_to_number = { number_to_day[idx]: idx
                  for idx in range(len(number_to_day) }

class Person:
    def __init__(self, name, email, 




class Roster:
    def __init__(self, person_list):
