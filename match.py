'''A student is represented as a dictionary, pulled straight from the
database. There's a dictionary of them, keyed by their email
address. The inter-student scores are stored in a dictionary whose
keys are pairs (tuples) of student emails. Both scores are redundantly
stored, so that it's easy to look them up.

The problem:

Given a set of "slots" that each student is available for pair
programming, find a matching where each student is paired with another
student such that the overlap between partners is maximized. The
definitions of the score for the overlap between two people and the
score for a complete matching are open to interpretation. 

API:

read_students(conn, course): read a list of students and their
    schedules from the database.

compute_all_scores(student_list): pre-computes all the pairwise scores

get_score(stud_a, stud_b):  args are student dictionaries


compute_schedule_score(schedule): computes the score for a complete
    matching, which is the sum of the pairwise scores, plus the lowest one
    again, bumping up its importance

ALGORITHMS:

All take a list of students as an argument, defaulting to all_students

matching_greedy(): a conventional greedy algorithm, where we pair A with
   whatever overlaps best, then on to the next one (probably B).

matching_exhaustive(): enumerates all possible pairing, computes

matching_two_greedy(): partly greedy and partly exhaustive. Considers
    the two best overlaps combined with all two_greedy matchings based on
    that.

TO DO:

Make the student into a proper object, instead of committing to a
dictionary

'''

import random
import cs304dbi as dbi
dbi.conf('scottdb')

days_of_the_week = 'Sun,Mon,Tue,Wed,Thu,Fri,Sat'.split(',')

all_slots = "900,930,1000,1030,1100,1130,1200,1230,1300,1330,1400,1430,1500,1530,1600,1630,1700,1730,1800,1830,1900,1930,2000,2030,2100,2130,2200,2230,2300,2330".split(',')

all_students = None

def read_students(conn, course):
    '''returns a dictionary of all students, each represented as a dictionary'''
    dic = {}
    curs = dbi.dict_cursor(conn)
    # both the numeric and string value
    nrows = curs.execute('''select course, student_email, student_name,
                                   sun+0 as sun_i, mon+0 as mon_i, tue+0 as tue_i, wed+0 as wed_i, thu+0 as thu_i, fri+0 as fri_i, sat+0 as sat_i,
                                   sun as sun_s, mon as mon_s, tue as tue_s, wed as wed_s, thu as thu_s, fri as fri_s, sat as sat_s
                            from when_to_pair
                            where course = %s''',
                         [course])
    for row in curs.fetchall():
        dic[row['student_email']] = row
    return dic

def decode_day_schedule(day_sched_int):
    '''returns list of slots of a day schedule, equivalent to the integer presentation of a day schedule'''
    slots = []
    for i,slot in enumerate(all_slots):
        slot_val = 1 << i
        if day_sched_int & slot_val:
            slots.append(slot)
    return slots

def student_to_str(stud):
    result = stud['student_name'] + ' on\n'
    for day in days_of_the_week:
        dic_key = f'{day}_s'
        if dic_key not in stud:
            stud[dic_key] = decode_day_schedule(stud[f'{day}_i'])
        slots = stud[dic_key]
        result += f' {day}: {slots}\n'
    return result
    

# ================================================================

def day_score(sched_a, sched_b):
    '''args are ints, representing two student schedules for the same
    day. The score adds 1 for each overlap (each is 30 minutes) and
    subtracts half the number of overlaps, so a single 2-hour overlap
    counts for 3 (4-1), while two 1-hour overlaps counts for 2 (4-2)
    and four 30-minute overlaps counts for zero.

    '''
    day_overlap = sched_a & sched_b
    # print(f'{day_overlap=}')
    # bit_count is python 3.10, so we'll use this instead
    bit_count = bin(day_overlap).count('1')
    # loop instead to count both at once
    overlap_count = 0
    overlap_sum = 0
    prev_overlap = False    # true if continuing the previous session
    for i,slot in enumerate(all_slots):
        slot_val = 1 << i
        if (sched_a & slot_val and
            sched_b & slot_val):
            # an overlap!
            # print(f'overlap for {i=}')
            # print(f'{slot_val=}')
            overlap_sum += 1
            if not prev_overlap:
                # start a new session
                prev_overlap = True
                overlap_count += 1
        else:
            # gap
            prev_overlap = False
    # print(f'{overlap_count=} and {overlap_sum=}')
    return overlap_sum - overlap_count
    
def day_score_test():
    a = 15
    b = 15
    assert day_score(a, b) == 3
    b = b << 1
    assert day_score(a, b) == 2
    b = b << 1
    assert day_score(a, b) == 1
    b = b << 1
    assert day_score(a, b) == 0

    # two sessions
    a = 15 << 6
    a += 15
    b = a
    assert day_score(a, b) == 6
    
    

def overlap_score(stud_a, stud_b):
    '''Compute the score for the overlap of two students. Returns a number. Non side-effecting.'''
    score = 0
    for day in days_of_the_week:
        day = day.lower()
        key = f'{day}_i'
        sched_a = stud_a[key]
        sched_b = stud_b[key]
        score += day_score(sched_a, sched_b)
    return score

# ================================================================
# Triangle tables with each entry being the overlap_score for that
# pair of students.

def pair_overlap_table(student_list):
    for s in student_list:
        # adapted from time_sets.py
        sum = 0
        for day in days_of_the_week:
            day = day.lower()+'_i' # the integer
            # bit_count is python 3.10, so we'll use this instead
            bit_count = bin(s[day]).count('1')
            sum += bit_count
        s['total_free_time'] = sum
    # put the people with the least free time at the top
    student_list.sort(key=lambda s: s['total_free_time'])
    for i,s in enumerate(student_list):
        sname = s['student_name']
        semail = s['student_email']
        sfree = s['total_free_time']
        sover = overlap_score(s, s)
        print(f'{i}\t{semail}\t{sfree}\t{sover}\t{sname}')
    # triangle table
    sl = student_list
    n = len(student_list)
    tt = [ [ overlap_score(sl[i], sl[j])
             for i in range(n) ]
           for j in range(n) ]
    # header
    print('X', end='\t')
    for j in range(n):
        print(f' {j:2} ', end='|')
    print()
    # data
    for i in range(n):
        print(i, end='\t')
        for j in range(n):
            val = tt[i][j]
            print(f' {val:2} ', end='|')
        print()

    


# ================================================================
# Score storage

'''There are several approaches we could use: (1) dictionary with
tuple key, (2) nested dictionaries, (3) map each student to a small
integer (index in the class) and use a 2D array. Probably others. I'm
going for the last one, since it makes algorithms like the greedy
algorithm interesting.  '''

all_scores = None

# Option 1, dictionary keyed by tuples

def compute_all_scores_tuple_dictionary(student_list):
    '''return a dictionary of all the pairwise scores'''
    scores = {}
    for a in student_list:
        for b in student_list:
            if a is b:
                continue
            score = overlap_score(a,b)
            scores[(a,b)] = score
            scores[(b,a)] = score
    return scores

def get_score_tuple_dictionary(stud_a, stud_b):
    return all_scores[(stud_a, stud_b)]
            
# Option 3
# 2D array. Store both

def compute_all_scores_2d_array(student_list):
    for i,s in enumerate(student_list):
        s['index'] = i
    n = len(student_list)
    scores = [ [ 0 ] * n for i in range(n) ]
    for i,a in enumerate(student_list):
        for j,b in enumerate(student_list):
            if a is b:
                continue
            score = overlap_score(a,b)
            scores[i][j] = score
            scores[j][i] = score
    return scores

def get_score_2d_array(stud_a, stud_b):
    i = stud_a['index']
    j = stud_b['index']
    return all_scores[i][j]

# Choose option 3

def compute_all_scores(student_list=None):
    if student_list is None:
        student_list = all_students # use the global in not specified
    global all_scores
    all_scores = compute_all_scores_2d_array(student_list)
    return all_scores

def get_score(stud_a, stud_b):
    return get_score_2d_array(stud_a, stud_b)

# ================================================================

def make_test_student(course, letter):
    stud = {'course': course,
            'student_email': letter,
            'student_name': letter}
    set_random_schedule(stud)
    return stud

def random_schedule():
    limit = 1 << len(all_slots)
    return random.randint(0, limit-1)

def set_random_schedule(stud):
    for day in days_of_the_week:
        key = f'{day}_i'
        stud[key] = random_schedule()

def make_test_students(num_students, course='random'):
    studs = [ make_test_student(course, chr(ord('A')+i))
              for i in range(num_students) ]
    global all_students
    all_students = studs
    # store index in the universe
    for i,stud in enumerate(studs):
        stud['index'] = i
    # precompute overal scores
    compute_all_scores()
    return studs

def save_all_students(conn=None):
    if conn is None:
        dbi.conf('scottdb')
        conn = dbi.connect()
    curs = dbi.cursor(conn)
    for stud in all_students:
        day_scheds = [ stud[f'{day}_i']
                       for day in days_of_the_week ]
        vals = [ stud['course'], stud['student_email'], stud['student_name'] ]
        # twice
        vals.extend(day_scheds)
        vals.extend(day_scheds)
        curs.execute('''insert into when_to_pair values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        on duplicate key update
                        sun=%s, mon=%s, tue=%s, wed=%s, thu=%s, fri=%s, sat=%s''',
                     vals)
    conn.commit()

# ================================================================
# Schedule representation

'''A schedule is a dictionary with keys:

students: a list of student elements

matches (a list of pairs of student indexes, smaller first).

unmatched: a list of unmatched students, if any

score: The numeric score for the entire mat

Currently, the score is the sum of the scores for all pairs of
matches. A useful addition might be to add the smallest pair score a
second time, which gives a benefit to maximizing that smallest
score. We could think of lots of other schedule scores.

To handle a second schedule avoiding repeats, we can throw the matches
from previous schedules into the 'matches' list. Hmm. All the more
reason to make that more efficient. Yeah, I've switched to 2D array.

'''

def make_schedule(student_list=None):
    if student_list is None:
        student_list = all_students # use the global if not specified
    n = len(student_list)
    return {'students': student_list[:], # use a copy, just in case
            'unmatched': student_list[:], # use a copy, so we can remove from it
            'matched': [ [False] * n
                         for i in range(n) ],
            'score': 0}

def match_two(schedule, stud_a, stud_b):
    '''Remove them both from unmatched, and add them to matched.'''
    i = stud_a['index']
    j = stud_b['index']
    schedule['matched'][i][j] = True
    schedule['matched'][j][i] = True
    schedule['unmatched'].remove(stud_a)
    schedule['unmatched'].remove(stud_b)

def match_two_ints(schedule, stud_i, stud_j):
    '''Remove them both from unmatched, and add them to matched.'''
    schedule['matched'][stud_i][stud_j] = True
    schedule['matched'][stud_j][stud_i] = True
    schedule['unmatched'].remove(schedule['students'][stud_i])
    schedule['unmatched'].remove(schedule['students'][stud_j])

def compute_schedule_score(schedule):
    sched_score = 0
    lowest_overlap_score = 1_000_000_000
    students = schedule['students']
    n = len(students)
    matched = schedule['matched']
    compute_all_scores(students) # precompute all pairs
    for i in range(n):
        for j in range(i,n):
            if matched[i][j]:
                score = get_score(students[i], students[j])
                # print(f'{score=}')
                if score < lowest_overlap_score:
                    lowest_overlap_score = score
                sched_score += score
    sched_score += lowest_overlap_score
    return sched_score

def make_schedule_from_matching(student_list, matching):
    '''A matching is a list of tuples'''
    sched = make_schedule(student_list)
    for pair in matching:
        match_two(sched, pair[0], pair[1])
    sched['score'] = compute_schedule_score(sched)
    return sched

def make_schedule_from_matching_ints(student_list, matching_ints):
    '''A matching is a list of tuples'''
    sched = make_schedule(student_list)
    for i,j in matching_ints:
        match_two_ints(sched, i, j)
    sched['score'] = compute_schedule_score(sched)
    return sched

def array2d_to_tuple_list(array2d, universe=None):
    if universe is None:
        universe = all_students
    n = len(array2d)
    assert n == len(universe)
    for i in range(n):
        for j in range(i+1,n):
            yield (universe[i], universe[j])

def elt_generator(tuple_list):
    for tup in tuple_list:
        yield tup[0]
        if len(tup) == 2:
            yield tup[1]

def tuple_list_to_array2d(tuple_list):
    # find the universe, first. 
    universe = list(elt_generator())
    n = len(universe)
    array2d = [ [False] * n
                for i in range(n) ]
    for tup in tuple_list:
        if len(tup) == 1:
            continue
        i = universe.index(tup[0])
        j = universe.index(tup[1])
        array2d[i][j] = True
        array2d[j][i] = True
    

def compute_schedule_score_from_tuple_list(tuple_list):
    sched_score = 0
    lowest_overlap_score = 1_000_000_000
    n = len(tuple_list)
    for tup in tuple_list:
        score = get_score(tup[0], tup[1])
        # print(f'{score=}')
        if score < lowest_overlap_score:
            lowest_overlap_score = score
        sched_score += score
    sched_score += lowest_overlap_score
    return sched_score
    

def schedule_to_str(schedule):
    '''For printing a schedule.'''
    result = ''
    students = schedule['students']
    n = len(students)
    matched = schedule['matched']
    for i in range(n):
        for j in range(i,n):
            if matched[i][j]:
                stud_a = students[i]
                stud_b = students[j]
                name_a = stud_a['student_name']
                name_b = stud_b['student_name']
                score = get_score(stud_a, stud_b)
                result += f'''{score}\t{name_a} with {name_b}\n'''
    if len(schedule['unmatched']) > 0:
        stud_solo = schedule['unmatched']
        result += 'unmatched:  ' + stud_solo['student_name'] + '\n'
    result += f'''schedule score: {schedule['score']}'''
    return result

# ================================================================
# Matching objects

class Matching:
    def __init__(self, student_list):
        self.student_list = student_list
        n = len(student_list)
        self.unpaired = student_list[:]
        self.pairs_array = [ [False] * n
                             for i in range(n) ]
        self.pairs = []         # a list of pairs of indexes, i < j
        self.lowest_pair = None
        self.score = 0

    def add_pair(self, stud_a, stud_b):
        i = stud_a['index']
        j = stud_b['index']
        self.pairs_array[i][j] = True
        self.pairs_array[j][i] = True
        self.unpaired.remove(stud_a)
        self.unpaired.remove(stud_b)

    def remove_pair(self, stud_a, stud_b):
        i = stud_a['index']
        j = stud_b['index']
        self.pairs_array[i][j] = False
        self.pairs_array[j][i] = False
        self.unpaired.append(stud_a)
        self.unpaired.append(stud_b)

    # should we return indexes or elements? The former is more
    # efficient but more cumbersome
    def all_pairs(self):
        n = len(self.student_list)
        for i in range(n):
            for j in range(i,n):
                if self.pairs_array[i][j]:
                    yield (i,j)

    def calculate_score(self):
        students = self.student_list
        paired = self.pairs_array
        n = len(self.student_list)
        total_score = 0
        lowest_score = 1_000_000_000
        lowest_pair = None
        pairs = []
        for i in range(n):
            for j in range(i,n):
                if paired[i][j]:
                    stud_a = students[i]
                    stud_b = students[j]
                    name_a = stud_a['student_name']
                    name_b = stud_b['student_name']
                    pairs.append((i, j))
                    score = get_score(stud_a, stud_b)
                    if score < lowest_score:
                        lowest_score = score
                        lowest_pair = (stud_a, stud_b)
                    total_score += score
        total_score += lowest_score
        self.score = total_score
        self.pairs = pairs
        self.lowest_pair = lowest_pair
        self.lowest_score = lowest_score
        return total_score

    def random_pairing(self):
        # steadily shrink the length of the unpaired list
        unpaired = self.unpaired
        while len(unpaired) > 1:
            '''To avoid the issue of randomly generating the same
            index twice, which will become increasingly common as the
            number of unpaired elements shrinks, we generate a random
            row number (n-1 possibilities) and a random column number
            (n-2 possibilities). If the col==row, we set col to n-1
            (since it can't be n-1, and that's an unused value). Then
            make row<col.'''
            n = len(unpaired)
            row = random.randint(0,n-1)
            col = random.randint(0,n-2)
            if row == col:
                col = n-1       # since it can't be
            if col < row:
                row,col = col,row
            assert 0 <= row < col < n
            # don't use .pop. They will be removed by the add_pair method, below
            b = unpaired[col]
            a = unpaired[row]
            # print('before')
            # for p in self.all_pairs():
            #     print(p, sep=' ')
            # print(f'''pairing a={a['student_name']} ({row}) with b={b['student_name']} ({col})''')
            self.add_pair(a,b)
            # print('after')
            # for p in self.all_pairs():
            #     print(p, sep=' ')

    def __str__(self):
        # have to precompute the score so that we know what the lowest
        # is, so we can add an asterisk
        total = self.calculate_score()
        students = self.student_list
        lowest_pair = self.lowest_pair
        result = ''
        for i,j in self.pairs:
            stud_a = students[i]
            stud_b = students[j]
            score = get_score(stud_a, stud_b)
            name_a = stud_a['student_name']
            name_b = stud_b['student_name']
            ## add an asterisk to the lowest pair
            if stud_a == lowest_pair[0] and stud_b == lowest_pair[1]:
                result += f'''{name_a} with {name_b} ({score}) **\n'''
            else:
                result += f'''{name_a} with {name_b} ({score})\n'''
        for solo in self.unpaired:
            result += 'unmatched:  ' + solo['student_name'] + '\n'
        result += f'''score: {total}\n'''
        result += f'''lowest: {self.lowest_score}\n'''
        return result

def test_random_pairing(trials=1000, elts='a b c d e f'.split()):
    '''This seems to work.'''
    counts = {}
    for i in range(trials):
        copy = elts[:]
        while len(copy) > 2:
            n = len(copy)
            row = random.randint(0,n-1)
            col = random.randint(0,n-2)
            if col == row:
                col = (n-1)
            if row > col:
                row, col = col, row
            # print(row, col, n)
            assert 0 <= row < col < n
            b = copy.pop(col)
            a = copy.pop(row)
            pair = (a, b)
            counts[pair] = counts.get(pair,0) + 1
            
    for pair in sorted(counts.keys()):
        print(pair, counts[pair])
    return counts

# ================================================================
# Matching Algorithms.

'''There are *lots* of possibilities. In fact, it would be fun to make
this a running example in an algorithms course. But for now, I'm just
going to try some.

Remember, Murphy's law says the number of students will always be odd,
so make sure you account for that in the algorithm.

'''

# Option 1: Greedy

def matching_greedy(students=None):
    if students is None:
        students = all_students
    m = Matching(students)
    unmatched = m.unpaired # we are assuming that aliasing will work for us
    while len(unmatched) > 1:
        for stud in unmatched:
            best_overlap_score = -1
            best_overlap_other = None
            for other in unmatched:
                this_score = get_score(stud, other)
                if this_score > best_overlap_score:
                    best_overlap_score = this_score
                    best_overlap_other = other
            m.add_pair(stud, best_overlap_other)
    m.calculate_score()
    return m

greedy_schedule = None

def matching_greedy_test(n):
    make_test_students(n)
    compute_all_scores()
    global greedy_schedule
    greedy_schedule = matching_greedy()
    print(schedule_to_str(greedy_schedule))
    return greedy_schedule

# Option 2: Exhaustive

'''This creates O(n!) schedules and then chooses the best. This will
be our gold standard. But we need to make sure we don't solve the same
subproblem more than once.  For example, with 8 students we could
choose (A,B) and then (C,D), leaving E,F,G,H as a subproblem, or we
could choose (A,C) and then (B,D) leaving the same subproblem.

The solution to that E,F,G,H subproblem is not a single schedule, but
a list of schedules. The caller can iterate over that list, adding
more pairs to each.

Note that we could have an odd number of students, so that means, with
just 3 students, we have three matchings: [ (a,b) (c) ], [ (a,c), b ]
and [ (b,c), a ]. But I think we can try removing each element as a
singleton, and then deal only with pairs.

We could use a dynamic programming approach, indexing an array with
the set of unmatched students. The array needs to be of size 2^N where
N is the number of students. If N starts getting near 30, we are
screwed. So, we'll limit this algorithm to N <= 16.

For simplicity, we'll modularize this, so that we generate all
possible matchings, and then, for each matching, we'll compute a
schedule and a score for it.
'''

def copy_remove(list, elt):
    copy = list[:]
    copy.remove(elt)
    return copy

def match_count(n):
    if n <= 2:
        return 1
    if n % 2 == 1:
        return n * match_count(n-1)
    return (n-1) * match_count(n-2)


'''
1 => 1
2 => 1
3 => 3
4 => 3
5 => 15
6 => 15
7 => 105
8 => 105
9 => 945
10 => 945
11 => 10,395
12 => 10,395
13 => 135,135
14 => 135,135
15 => 2,027,025
16 => 2,027,025
17 => 34,459,425
18 => 34,459,425
19 => 654,729,075
20 => 654,729,075
21 => 13,749,310,575
22 => 13,749,310,575
23 => 316,234,143,225
24 => 316,234,143,225
25 => 7,905,853,580,625
26 => 7,905,853,580,625
27 => 213,458,046,676,875
28 => 213,458,046,676,875
29 => 6,190,283,353,629,375
30 => 6,190,283,353,629,375
'''

## It takes nearly 2 minutes just to enumerate the matches for n=18
## It takes incredibly long (41 minutes?) to enumerate the matches for n=19

def match_count_table(n):
    '''We're definitely not using an exhaustive algorithm for a class
    of 30! But *maybe* for a class of 20.'''
    for i in range(1,n+1):
        mc = match_count(i)
        print(f'{i} => {mc:,}')


def matchlist(elts):
    '''Return a list of all the matches drawn from elts, in canonical
    order, where each match is represented as a list of tuples. A
    singleton tuple, if any, will be the first tuple.'''
    n = len(elts)
    if n == 0:
        return []
    if n == 1:
        return [[(elts[0],)]]
    if n == 2:
        return [[(elts[0],elts[1])]]
    is_even = (n % 2) == 0
    if is_even:
        a = elts[0]
        rest = elts[1:]
        results = []
        for b in rest:
            first_tuple = (a,b)
            others = copy_remove(rest, b)
            for matches in matchlist(others):
                matches.insert(0, first_tuple)
                results.append( matches )
        return results
    if not is_even:
        results = []
        for a in elts:
            first_tuple = (a,)
            others = copy_remove(elts, a)
            for matches in matchlist(others):
                matches.insert(0, first_tuple)
                results.append( matches )
        return results


def matchlist_generator(elts):
    '''Returns a generator that will yield all the matches drawn from
    elts, in canonical order, where each match is represented as a
    list of tuples. A singleton tuple, if any, will be the first
    tuple.

    '''
    n = len(elts)
    if n == 0:
        yield []
    if n == 1:
        yield [[(elts[0],)]]
    if n == 2:
        yield [[(elts[0],elts[1])]]
    is_even = (n % 2) == 0
    if is_even:
        a = elts[0]
        rest = elts[1:]
        for b in rest:
            first_tuple = (a,b)
            others = copy_remove(rest, b)
            for matches in matchlist(others):
                matches.insert(0, first_tuple)
                yield matches
    if not is_even:
        results = []
        for a in elts:
            first_tuple = (a,)
            others = copy_remove(elts, a)
            for matches in matchlist(others):
                matches.insert(0, first_tuple)
                yield matches

def matchlist_print(elts):
    for match in matchlist_generator(elts):
        print(match)

# this is also useful for timing the generation of millions of matches

def matchlist_count(elts):
    cnt = 0
    for match in matchlist_generator(elts):
        cnt += 1
    return cnt

def encode_set(subset, universe):
    '''Return an integer representing the subset.'''
    result = 0
    for i in range(len(universe)):
        bit = 1 << i
        if universe[i] in subset:
            result = result | bit
    return result

def matching_exhaustive(student_list=None):
    if student_list is None:
        student_list = all_students
    # a match is a list of tuples
    best_match = None
    best_score = 0
    for match in matchlist_generator(student_list):
        score = compute_schedule_score_from_tuple_list(match)
        if score > best_score:
            best_match = match
            best_score = score
            # print(f'new best: {best_score}')
    # sched = make_schedule_from_matching(all_students, best_match)
    m = Matching(student_list)
    for a,b in best_match:
        m.add_pair(a,b)
    m.calculate_score()
    return m
    
# ================================================================
# Approximation: This is between greedy and optimal.

'''The idea is that instead of just choosing the best match for the
current student and going on (greedy), we choose the 2 best matches,
and consider all possibilities given those two matches. Thus, if there
are N people in the class (assume N is even), there will be N/2 pairs
and so we'll consider 2^(N/2-1) possible matchings. Then we choose the
best among those.

More generally, we could choose the K best matches and consider all
K^(N/2) possible matchings. As K gets closer to N, this gets closer to
optimal.

I'll call this K-greedy, but I'll start with two-greedy
'''

def two_greedy_matchings_recursive(student_list=None):
    '''Returns a generator of all matchings where the pairs are always
    among the two best possible matchings, given earlier
    choices. pairwise_score is a function taking two arguments and
    returning the pairwise score for those two students.

    Result seems to generate 2^(n/2-1) matchings where n is
    len(student_list). For example, 10 students is 16=2^4 while 20
    students is 512=2^9 and 30 students is 16,384=2^14, which is
    eminently do-able.

    '''
    if student_list is None:
        if all_students is None:
            make_test_students(20, 'twenty')
        student_list = all_students
    pair_scores = []
    n = len(student_list)
    if n == 2:
        # result is always a list of tuples
        yield [tuple(student_list)]
    for i in range(n):
        for j in range(i+1,n):
            a = student_list[i]
            b = student_list[j]
            pair_scores.append((a, b, overlap_score(a,b)))
    pair_scores.sort(key=lambda stud: stud[2],
                     reverse=True)
    best = pair_scores[:2]      # could be K
    indent = '    ' * (20 - len(student_list))
    for pair in best:
        a,b,s = pair
        # print(f'''{indent} trying {a['student_email']} and {b['student_email']} with score {s}''')
        copy = student_list[:]
        copy.remove(a)
        copy.remove(b)
        for other in two_greedy_matchings_recursive(copy):
            other.insert(0, (a,b))
            other_names = [ (t[0]['student_name'],
                             t[1]['student_name'])
                            for t in other ]
            # print(f'''{indent} {other_names=}''')
            yield other

def matching_two_greedy(student_list=None):
    if student_list is None:
        student_list = all_students
    cnt = 0
    best_match = None
    best_score = 0
    for match in two_greedy_matchings_recursive(student_list):
        score = compute_schedule_score_from_tuple_list(match)

        cnt += 1
        names = [ (t[0]['student_name'],
                   t[1]['student_name'])
                  for t in match ]
        # print(f'{cnt}: {score=} {names}')

        if score > best_score:
            best_match = match
            best_score = score
            # print(f'new best: {best_score}')
    # sched = make_schedule_from_matching(all_students, best_match)
    m = Matching(student_list)
    for a,b in best_match:
        m.add_pair(a,b)
    return m


# ================================================================
# Improve

def matching_improve(matching):
    '''Unlike the earlier algorithms, this takes an existing matching
    and tries to improve it by considering all pairs of pairs, and if
    they are [(a,b),(c,d),...others] considers [(a,c),(b,d),...others]
    and [(a,d),(b,c) to see if either are any better.

    '''
    # we have to modify a copy or it's possible that adding/removing
    # pairs will mess up the iteration, though I think we never will
    # visit either of these again, so it might not matter.
    sl = matching.student_list
    improved = Matching(sl)
    for i,j in matching.all_pairs():
        # ick. There has to be a more efficient way to do this
        improved.add_pair(sl[i], sl[j])
    score_before = matching.calculate_score()
    for i,pi in enumerate(matching.all_pairs()):
        for j,pj in enumerate(matching.all_pairs()):
            if j <= i:
                continue
            # pi and pj contain indexes, so need to dereference
            a,b = sl[pi[0]], sl[pi[1]]
            c,d = sl[pj[0]], sl[pj[1]]
            score1 = get_score(a,b)+get_score(c,d)
            score2 = get_score(a,c)+get_score(b,d)
            score3 = get_score(a,d)+get_score(b,c)
            if score1 >= score2 and score1 >= score3:
                # no improvement possible
                continue
            improved.remove_pair(a,b)
            improved.remove_pair(c,d)
            if score2 > score3:
                improved.add_pair(a,c)
                improved.add_pair(b,d)
                print(f'swapping A,B and C,D for A,C and B,D')
            else:
                improved.add_pair(a,d)
                improved.add_pair(b,c)
                print(f'swapping A,B and C,D for A,D and B,C')
            # debug
            score_after = improved.calculate_score()
            print(f'score improved from {score_before} to {score_after}')
            assert score_before < score_after
            return improved, False
    # return original and True if no improvement
    return matching, True

def matching_local_optimum(matching):
    score1 = matching.calculate_score()
    done = False
    while not done:
        matching, done = matching_improve(matching)
        print(done)
    score2 = matching.calculate_score()
    print(f'Overall, score improved from {score1} to {score2}')
    return matching

def matching_hill_climbing_random_start(student_list=None):
    if student_list is None:
        student_list = all_students
    matching1 = Matching(student_list)
    matching1.random_pairing()
    print(matching1)
    return matching_local_optimum(matching1)

# ================================================================
# 

def bakeoff(n=16):
    make_test_students(n, 'bakeoff')
    # if n <= 16:
    #     m1 = matching_exhaustive()
    #     print('exhaustive:', m1, sep="\n")
    # m2 = matching_two_greedy()
    # print('two greedy:', m2, sep="\n")
    # m3 = matching_greedy()
    # print('greedy:', m3, sep="\n")
    #
    m4 = matching_hill_climbing_random_start()
    print('hill climbing', m4, sep="\n")

# ================================================================


cs304 = None
cs304s1 = None
cs304s2 = None

def tt_cs304():
    dbi.conf('scottdb')
    conn = dbi.connect()
    class_dict = read_students(conn, 'cs304-f24')
    global cs304
    cs304 = list(class_dict.values())
    for i,s in enumerate(cs304):
        s['index'] = s
    pair_overlap_table(cs304)
    global cs304s1
    cs304s1 = make_schedule_from_matching_ints(
        cs304, [(0,12), (1,10), (2,19), (3,9), (4,14), (5,16), (6,8), (7,11), (13,15), (17,18), (20,21), (22,23), (24,25), (26,27)])
    # print(schedule_to_str(cs304s1))
    global cs304s2
    cs304s2 = make_schedule_from_matching_ints(
        cs304, [(0,26), (1,25), (2, 19), (3,27), (4,20), (5,24), (6,21), (7,16), (8,22), (9,23), (10,18), (11,12), (13,15), (14,17)])
    print(schedule_to_str(cs304s2))
            

def main():
    dbi.conf('scottdb')
    conn = dbi.connect()
    global all_students
    all_students = read_students(conn, 'cs304-f24')
    compute_all_scores(all_students)

if __name__ == '__main__':
    # u = list('abcdefghiklmnopqrst')
    # print(len(u))
    # print(matchlist_count(u))
    tt_cs304()
