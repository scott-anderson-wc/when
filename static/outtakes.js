function getStudents() {
    fetch(studentsUrl)
        .then((response) => {
            if (response.status === 200) {
                // global
                students = response.json();
                formatStudents();
            } else {
                throw new Error("Something went wrong on API server!");
            }
        })
        .then((response) => {
            console.debug('server response', response);
        })
        .catch((error) => {
            console.error(error);
        });
}

function formatStudents() {
    let select = $("[name=student]");
    for(student of students) {
        let elt = $("<option>")
            .attr('value', student.email)
            .text(student.name);
        select.append(elt);
    }
}

