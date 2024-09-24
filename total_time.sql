use scottdb;

select course,student_name,(bit_count(sun)+bit_count(mon)+bit_count(tue)+bit_count(wed)+bit_count(thu)+bit_count(fri)+bit_count(sat))/2 as total
from when_to_pair
where course='cs304-f24'
order by total desc;



