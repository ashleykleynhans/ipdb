"""
Create aliases table
"""

from yoyo import step

__depends__ = {'ipdb_20200108_01_Xro8I-create-ips-table'}

steps = [
    step("""CREATE TABLE aliases (
                id INT UNSIGNED NOT NULL AUTO_INCREMENT,
                ip INT UNSIGNED NOT NULL,
                alias VARCHAR(100) NOT NULL,
                last_modified TIMESTAMP NOT NULL,
                PRIMARY KEY(id),
                FOREIGN KEY (ip) REFERENCES ips(id))""",
         "DROP TABLE aliases")
]
