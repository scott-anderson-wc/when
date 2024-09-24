'''If time slots are no shorter than 30 minutes, and they start at 9am
and go to midnight, that's 15 hours or 30 half-hours, so the time
slots of a day can be represented in a 32-bit integer. Very cool. So,
we are going to use that internally and in the database.

We'll allow for time slots for all 7 days of the week, so we'll have a
list of 7 integers.

The class below is an abstraction that allows us the ability to pass
these things around and print them without getting into some of the
translations from ints to lists of timeslots and vice versa.

'''

import random
from day_number import *
from typing import Union

all_slots = "900,930,1000,1030,1100,1130,1200,1230,1300,1330,1400,1430,1500,1530,1600,1630,1700,1730,1800,1830,1900,1930,2000,2030,2100,2130,2200,2230,2300,2330".split(',')

class Time_Set:
    def __init__(self, avail: list[int] = None):
        self._avail = avail

    def total_free_time(self):
        '''return the number of available half-hour slots'''
        if self._avail is None:
            return 0
        sum = 0
        for day in range(7):
            # bit_count is python 3.10, so we'll use this instead
            bit_count = bin(self._avail[day]).count('1')
            sum += bit_count
        return sum

    def set_avail_day(self, day: int, slots: int):
        '''set the availability for a particular day'''
        if self._avail is None:
            self._avail = [ 0 for i in range(7) ]
        self._avail[day] = slots

    def avail_int(self, day: int):
        '''returns the availability as an integer'''
        if self._avail is None:
            return 0
        return self._avail[day]

    def avail(self, day: int):
        '''return a list of slots available on a particular day'''
        if self._avail is None:
            return []
        slots: list = []
        day_sched: int = self._avail[day]
        for i,slot in enumerate(all_slots):
            slot_val: int = 1 << i
            if day_sched & slot_val:
                slots.append(slot)
        return slots

    def random_availability(self):
        limit = 1 << len(all_slots)
        self._avail = [ random.randint(0, limit) for i in range(7) ]

    def __repr__(self):
        val: str = ''
        for day in range(7):
            val += number_to_day[day] + '\t' + ','.join(self.avail(day)) + '\n'
        return val

def time_overlap(ts1, ts2):
    ts3 = Time_Set()
    for day in range(7):
        intersect = ts1.avail_int(day) & ts2.avail_int(day)
        ts3.set_avail_day(day, intersect)
    return ts3

def distance_table(n:int=10):
    '''Generate N random schedules and sort them by total free time,
    and also produce a triangle table of their overlaps.'''
    ts_list = [ Time_Set() for i in range(n) ]
    for ts in ts_list:
        ts.random_availability()
    ts_list.sort(key=lambda ts: ts.total_free_time())
    for ts in ts_list:
        print(ts)
        print(ts.total_free_time())
    # triangle table
    tt = [ [ time_overlap(ts_list[i], ts_list[j])
             for i in range(n) ]
           for j in range(n) ]
    # header
    print('X', end='\t')
    for j in range(n):
        print(j, end='\t')
    print()
    # data
    for i in range(n):
        print(i, end='\t')
        for j in range(n):
            print(tt[i][j].total_free_time(), end='\t')
        print()
    
'''

            if j <= i:
                print(' ', end='\t')
            else:
                ts = time_overlap(ts_list[i], ts_list[j])
                print(ts.total_free_time(), end='\t')
'''


if __name__ == '__main__':
    ts1 = Time_Set(None)
    ts1.random_availability()
    print(repr(ts1))
    print(ts1)
    
    
