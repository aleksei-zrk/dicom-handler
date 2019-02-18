from pony.orm import (
    Database,
    Required, Optional, PrimaryKey, Set, set_sql_debug, db_session
)

db = Database()


class PatientData(db.Entity):

    id = PrimaryKey(str, 15)
    name = Required(str, 50)
    sex = Required(str, 10)
    body_part = Required(str, 10)



