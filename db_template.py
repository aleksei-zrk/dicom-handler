from pony.orm import (
    Database, Required, PrimaryKey, db_session
)

db = Database()


class PatientData(db.Entity):

    id = PrimaryKey(str, 15)
    name = Required(str, 50)
    sex = Required(str, 10)
    birthday = Required(str, 20)
    body_part = Required(str, 10)
    study_date = Required(str, 20)



