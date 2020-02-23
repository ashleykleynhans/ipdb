"""
Create ips table
"""

from yoyo import step

__depends__ = {}

steps = [
    step("""CREATE TABLE ips (
                id INT UNSIGNED NOT NULL AUTO_INCREMENT,
                ip VARCHAR(15) NOT NULL,
                hostname VARCHAR(100) NOT NULL,
                category VARCHAR(200) NOT NULL,
                comment VARCHAR(200) NOT NULL,
                last_modified TIMESTAMP NOT NULL,
                PRIMARY KEY(id))""",
         "DROP TABLE ips")
]
