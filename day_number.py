# Days of the week are numbered starting at zero for Sunday, abbreviate to 3 letters

number_to_day = 'sun,mon,tue,wed,thu,fri,sat'.split(',')

# Dictionary mapping day names to their index

day_to_number = { number_to_day[idx]: idx
                  for idx in range(len(number_to_day)) }
