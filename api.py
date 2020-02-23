import bottle
from bottle import response, request, app
from bottlejwt import JwtPlugin
import bottle_mysql
import re
import json
import codecs
import configparser

# Initialise Config File
cfg = configparser.RawConfigParser()
cfg.read('.env')

# Get DB Configuration
DB_USER = cfg.get('database', 'DB_USER')
DB_PASS = cfg.get('database', 'DB_PASS')
DB_HOST = cfg.get('database', 'DB_HOST')
DB_NAME = cfg.get('database', 'DB_NAME')

# Get API Configuration
API_USER = cfg.get('api', 'API_USER')
API_PASS = cfg.get('api', 'API_PASS')

# IP Address Validation Regex (used globally)
ippattern = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')


def validation(auth, auth_value):
    """Validate the JWT Authentication"""
    if 'username' in auth and auth[auth_value] == API_USER:
        return True

    return False


# Initialise the Bottle App, and add the MySQL and JWT plugins
app = bottle.Bottle()
plugin = bottle_mysql.Plugin(dbuser=DB_USER, dbpass=DB_PASS, dbname=DB_NAME, dbhost=DB_HOST)
app.install(plugin)
app.install(JwtPlugin(validation, API_PASS, algorithm='HS256'))


_allow_origin = '*'
_allow_methods = 'PUT, GET, POST, DELETE, OPTIONS'
_allow_headers = 'Authorization, Origin, Accept, Content-Type, X-Requested-With'


@app.hook('after_request')
def enable_cors():
    """Add headers to enable CORS"""

    response.headers['Access-Control-Allow-Origin'] = _allow_origin
    response.headers['Access-Control-Allow-Methods'] = _allow_methods
    response.headers['Access-Control-Allow-Headers'] = _allow_headers


@app.route('/', method='OPTIONS')
@app.route('/<path:path>', method='OPTIONS')
def options_handler(path=None):
    return


@app.route('/', method=['GET'])
def index_hander():
    """Handles index"""
    data = {
        'API':     'IP API',
        'Version': 'v1'
    }

    return json_success(data)


@app.route('/ips', method='POST', auth="username")
def ip_creation_handler(db, auth):
    """Handles ip creation"""
    try:
        # parse input data
        try:
            data = request.json
        except Exception:
            raise ValueError

        if data is None:
            raise ValueError

        # extract and validate ip
        try:
            if ippattern.match(data['ip']) is None:
                raise ValueError
            ip = data['ip']
            hostname = data['hostname']

            if 'category' not in data:
                category = data['category']
            else:
                category = ''

            if 'comment' not in data:
                comment = data['comment']
            else:
                comment = ''

            if 'aliases' not in data:
                aliases = []
            else:
                aliases = data['aliases']

            # aliases must be a list/array of aliases
            if len(aliases) and not isinstance(aliases, list):
                raise ValueError
        except (TypeError, KeyError):
            raise ValueError

        # check for existence
        db.execute('SELECT * FROM ips WHERE ip = %(ip)s', {'ip': ip})
        row = db.fetchone()

        if row:
            # if ip already exists, return 409 Conflict
            raise KeyError(409)

        ip_data = {
            'ip': ip,
            'hostname': hostname,
            'aliases': aliases,
            'category': category,
            'comment': comment
        }

        db.execute('INSERT INTO ips (ip, hostname, category, comment) VALUES (%(ip)s, %(hostname)s, %(category)s, %(comment)s)', ip_data)
        db.execute('SELECT last_insert_id() as ID')
        new_id = db.fetchone()['ID']

        for alias in aliases:
            alias_data = {
                'ip': new_id,
                'alias': alias
            }

            db.execute('INSERT INTO aliases (ip, alias) VALUES (%(ip)s, %(alias)s)', alias_data)

        # return 200 Success
        return json_success(ip_data)

    except ValueError:
        return json_error(400, 'error', 'Bad Request', 'BAD_REQUEST')

    except KeyError as e:
        if e.args[0] == 409:
            return json_error(409, 'error', 'IP Already Exists', 'IP_ALREADY_EXISTS')
        else:
            return json_error(500, 'error', 'Internal Server Error', 'INTERNAL_SERVER_ERROR')


@app.route('/aliases/<ip>', method='POST', auth="username")
def alias_creation_handler(ip, db, auth):
    """Handles ip alias creation"""
    try:
        # parse input data
        try:
            data = request.json
        except Exception:
            raise ValueError

        if data is None:
            raise ValueError

        # extract and validate alias
        try:
            if ippattern.match(ip) is None:
                raise ValueError

            if data['alias'] is None:
                raise ValueError

            alias = data['alias']
        except (TypeError, KeyError):
            raise ValueError

        # check for existence of ip
        db.execute('SELECT * FROM ips WHERE ip = %(ip)s', {'ip': ip})
        ip_row = db.fetchone()

        if not ip_row:
            raise KeyError(404)

        data = {
            'ip': ip_row['id'],
            'alias': alias
        }

        # check for existence of alias
        db.execute('SELECT * FROM aliases WHERE alias = %(alias)s AND ip = %(ip)s', data)
        alias_row = db.fetchone()

        if alias_row:
            raise KeyError(409)

        db.execute('INSERT INTO aliases (ip, alias) VALUES (%(ip)s, %(alias)s)', data)

        # return 200 Success
        return json_success(data)

    except ValueError:
        return json_error(400, 'error', 'Bad Request', 'BAD_REQUEST')

    except KeyError as e:
        if e.args[0] == 404:
            return json_error(404, 'error', 'Not Found', 'NOT_FOUND')
        elif e.args[0] == 409:
            return json_error(409, 'error', 'Alias Already Exists', 'ALIAS_ALREADY_EXISTS')
        else:
            return json_error(500, 'error', 'Internal Server Error', 'INTERNAL_SERVER_ERROR')


@app.route('/ips/<ip>', method='GET', auth="username")
def ip_retrieval_handler(ip, db, auth):
    """Handles ip retrieval"""
    try:
        try:
            if ippattern.match(ip) is None:
                raise ValueError
        except (TypeError, KeyError):
            raise ValueError

        db.execute('SELECT * FROM ips WHERE ip = %(ip)s', {'ip': ip})
        ip_row = db.fetchone()

        if not ip_row:
            raise KeyError(404)

        db.execute('SELECT * FROM aliases WHERE ip = %(ip)s ORDER BY alias', {'ip': ip_row['id']})
        alias_rows = db.fetchall()
        aliases = []

        for alias in alias_rows:
            aliases.append(alias['alias'])

        return json_success({
            'ip': ip_row['ip'],
            'hostname': ip_row['hostname'],
            'aliases': aliases,
            'category': ip_row['category'],
            'comment': ip_row['comment'],
        })

    except ValueError:
        return json_error(400, 'error', 'Bad Request', 'BAD_REQUEST')
    except KeyError as e:
        if e.args[0] == 404:
            return json_error(404, 'error', 'Not Found', 'NOT_FOUND')
        else:
            return json_error(500, 'error', 'Internal Server Error', 'INTERNAL_SERVER_ERROR')


@app.route('/ips', method='GET', auth="username")
def ip_listing_handler(db, auth):
    """Handles ip listing"""
    db.execute('SELECT * FROM ips ORDER BY ip')
    ip_rows = db.fetchall()
    ip_count = db.rowcount
    ips = []

    for ip_row in ip_rows:
        db.execute('SELECT * FROM aliases WHERE ip = %(ip)s ORDER BY alias', {'ip': ip_row['id']})
        alias_rows = db.fetchall()
        aliases = []

        for alias_row in alias_rows:
            aliases.append(alias_row['alias'])

        ip_data = {
            'ip': ip_row['ip'],
            'hostname': ip_row['hostname'],
            'aliases': aliases,
            'category': ip_row['category'],
            'comment': ip_row['comment'],
            'last_modified': str(ip_row['last_modified'])
        }

        ips.append(ip_data)

    return json_success({
        'count': ip_count,
        'ips': ips
    })


@app.route('/ips/network/<network>', method='GET', auth="username")
def allocated_ip_network_listing_handler(network, db, auth):
    """Handles listing of all IPs in use within a particular network"""
    ips = []

    db.execute('SELECT DISTINCT(ip) FROM ips WHERE ip LIKE %(network)s ORDER BY INET_ATON(ip)', {'network': network + '%'})
    rows = db.fetchall()

    for row in rows:
        ips.append(row['ip'])

    return json_success(ips)


@app.route('/ips/network/<network>/available', method='GET', auth="username")
def available_ip_network_listing_handler(network, db, auth):
    """Handles querying of available ips in the specified network"""
    assigned_ips = []
    available_ips = []

    db.execute('SELECT DISTINCT(ip) FROM ips WHERE ip LIKE %(network)s ORDER BY INET_ATON(ip)', {'network': network + '%'})
    rows = db.fetchall()

    for row in rows:
        assigned_ips.append(int(row['ip'].split('.')[-1]))

    for i in range(2, 254):
        if i not in assigned_ips:
            available_ips.append(network + '.' + str(i))

    return json_success(available_ips)


# Generate hosts file
@app.route('/hosts', method='GET', auth="username")
def generate_hosts_handler(db, auth):
    """Handles hosts generation"""
    db.execute('SELECT * FROM ips ORDER BY id')
    rows = db.fetchall()

    response.headers['Content-Type'] = 'text/plain'
    response.headers['Cache-Control'] = 'no-cache'
    response.status = 200

    hosts = "# -*- mode: conf -*-\n\n"
    hosts += "#######################\n"
    hosts += "# digital hosts start #\n"
    hosts += "#######################\n\n"
    hosts += "# See the README.md file in the project root before using this.\n"
    hosts += "# https://git.fnb.co.za/digital/ops/hosts\n\n"

    current_category = ''

    for row in rows:
        hostname = row['hostname']
        db.execute('SELECT * FROM aliases WHERE ip = %(ip)s ORDER BY alias', {'ip': row['id']})
        alias_rows = db.fetchall()

        for alias_row in alias_rows:
            hostname += ' ' + alias_row['alias']

        if row['category'] and row['category'] != current_category:
            hosts += "\n"
            hosts += "########################################################\n"
            hosts += "# {0:52} #\n".format(row['category'])
            hosts += "########################################################\n"
        elif not row['category'] and row['category'] != current_category:
            hosts += "\n"

        current_category = row['category']

        if row['comment']:
            hosts += "{0:16}  {1} # {2}\n".format(row['ip'], hostname, row['comment'])
        else:
            hosts += "{0:16}  {1}\n".format(row['ip'], hostname)

    hosts += "\n"
    hosts += "#####################\n"
    hosts += "# digital hosts end #\n"
    hosts += "#####################"

    return hosts


@app.route('/ips/<ip>', method='PUT', auth="username")
def ip_update_handler(ip, db, auth):
    """Handles ip updates"""

    try:
        # parse input data
        try:
            utf8reader = codecs.getreader('utf-8')
            data = json.load(utf8reader(request.body))
        except Exception:
            raise ValueError

        # extract and validate new ip
        try:
            if ippattern.match(ip) is None:
                raise ValueError
            hostname = data['hostname']
        except (TypeError, KeyError):
            raise ValueError

        # check whether the ip exists
        db.execute('SELECT * FROM ips WHERE ip = %(ip)s', {'ip': ip})
        row = db.fetchone()

        if not row:
            raise KeyError(404)

        if 'category' in data:
            category = data['category']
        else:
            category = row['category']

        if 'comment' in data:
            comment = data['comment']
        else:
            comment = row['comment']

        # check whether the new hostname already exists
        db.execute('SELECT * FROM ips WHERE hostname = %(hostname)s', {'hostname': hostname})
        row = db.fetchone()

        if row:
            return json_error(409, 'error', 'Hostname Already Associated with an IP', 'HOSTNAME_ALREADY_ASSOCIATED')

        # update the hostname
        data = {
            'ip': ip,
            'hostname': hostname,
            'category': category,
            'comment': comment
        }

        db.execute('UPDATE ips SET hostname = %(hostname)s, category = %(category)s, comment = %(comment)s WHERE ip = %(ip)s', data)

        # return 200 Success
        return json_success(data)

    except ValueError:
        return json_error(400, 'error', 'Bad Request', 'BAD_REQUEST')
    except KeyError as e:
        if e.args[0] == 404:
            return json_error(404, 'error', 'Not Found', 'NOT_FOUND')
        else:
            return json_error(500, 'error', 'Internal Server Error', 'INTERNAL_SERVER_ERROR')


@app.route('/aliases/<ip>/<alias>', method='PUT', auth="username")
def alias_update_handler(ip, alias, db, auth):
    """Handles alias updates"""

    try:
        # parse input data
        try:
            utf8reader = codecs.getreader('utf-8')
            data = json.load(utf8reader(request.body))
        except Exception:
            raise ValueError

        # extract and validate new ip
        try:
            if ippattern.match(ip) is None:
                raise ValueError

            if alias is None:
                raise ValueError

            new_alias = data['alias']
            current_alias = alias
        except (TypeError, KeyError):
            raise ValueError

        # check whether the ip exists
        db.execute('SELECT * FROM ips WHERE ip = %(ip)s', {'ip': ip})
        ip_row = db.fetchone()

        if not ip_row:
            raise KeyError(404)

        # check whether the current alias exists
        db.execute('SELECT * FROM aliases WHERE ip = %(ip)s AND alias = %(alias)s',
                   {'ip': ip_row['id'], 'alias': current_alias})

        alias_row = db.fetchone()

        if not alias_row:
            raise KeyError(404)

        # check whether the new alias already exists
        db.execute('SELECT * FROM aliases WHERE alias = %(alias)s', {'alias': new_alias})
        row = db.fetchone()

        if row:
            return json_error(409, 'error', 'Alias Already Associated with an IP', 'ALIAS_ALREADY_ASSOCIATED')

        # update the hostname
        data = {
            'row_id': alias_row['id'],
            'new_alias': new_alias
        }

        db.execute('UPDATE aliases SET alias = %(new_alias)s WHERE id = %(row_id)s', data)

        # return 200 Success
        return json_success(data)

    except ValueError:
        return json_error(400, 'error', 'Bad Request', 'BAD_REQUEST')
    except KeyError as e:
        if e.args[0] == 404:
            return json_error(404, 'error', 'Not Found', 'NOT_FOUND')
        else:
            return json_error(500, 'error', 'Internal Server Error', 'INTERNAL_SERVER_ERROR')


@app.route('/ips/<ip>', method='DELETE', auth="username")
def ip_deletion_handler(ip, db, auth):
    """Handles ip deletions"""
    try:
        try:
            if ippattern.match(ip) is None:
                raise ValueError
        except (TypeError, KeyError):
            raise ValueError

        db.execute('SELECT * FROM ips WHERE ip = %(ip)s', {'ip': ip})
        row = db.fetchone()

        if row:
            # Remove aliases
            db.execute('DELETE FROM aliases WHERE ip = %(ip)s', {'ip': row['id']})

            # Remove ip
            db.execute('DELETE FROM ips WHERE ip = %(ip)s', {'ip': ip})

            # return 200 Success
            return json_success({})
        else:
            raise KeyError(404)

    except ValueError:
        return json_error(400, 'error', 'Bad Request', 'BAD_REQUEST')
    except KeyError as e:
        if e.args[0] == 404:
            return json_error(404, 'error', 'Not Found', 'NOT_FOUND')
        else:
            return json_error(500, 'error', 'Internal Server Error', 'INTERNAL_SERVER_ERROR')


@app.route('/aliases/<ip>/<alias>', method='DELETE', auth="username")
def alias_deletion_handler(ip, alias, db, auth):
    """Handles alias deletions"""
    try:
        try:
            if ippattern.match(ip) is None:
                raise ValueError
        except (TypeError, KeyError):
            raise ValueError

        if alias is None:
            raise ValueError

        db.execute('SELECT * FROM ips WHERE ip = %(ip)s', {'ip': ip})
        ip_row = db.fetchone()

        if not ip_row:
            raise KeyError(404)

        query_data = {'ip': ip_row['id'], 'alias': alias}
        db.execute('SELECT * FROM aliases WHERE ip = %(ip)s AND alias = %(alias)s', query_data)
        alias_row = db.fetchone()

        if not alias_row:
            raise KeyError(404)

        # Remove alias
        db.execute('DELETE FROM aliases WHERE ip = %(ip)s AND alias = %(alias)s', query_data)

        # return 200 Success
        return json_success({})

    except ValueError:
        return json_error(400, 'error', 'Bad Request', 'BAD_REQUEST')
    except KeyError as e:
        if e.args[0] == 404:
            return json_error(404, 'error', 'Not Found', 'NOT_FOUND')
        else:
            return json_error(500, 'error', 'Internal Server Error', 'INTERNAL_SERVER_ERROR')


@app.error(403)
def error404(error):
    return json_error(403, 'error', 'Access Denied', 'ACCESS_DENIED')


@app.error(404)
def error404(error):
    return json_error(404, 'error', 'Not Found', 'NOT_FOUND')


# Uncomment this to enable debugging
# @app.error(500)
# def error500(error):
#     return json_error(500, 'error', 'Internal Server Error', 'INTERNAL_SERVER_ERROR')


def json_error(http_status, result, message, code):
    """Helper function to format JSON error responses"""
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = 'no-cache'
    response.status = http_status

    return json.dumps({
        'status':  result,
        'message': message,
        'code':    code
    })


def json_success(data):
    """Helper function to format JSON success responses"""
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = 'no-cache'
    response.status = 200
    return json.dumps(data)


def start_api():
    """Helper function to run the API and listen for incoming connections"""
    try:
        app.run(host='0.0.0.0', port=8000, reloader=True, debug=True)
    except Exception:
        bottle.response.headers['Content-Type'] = 'application/json'
        bottle.response.headers['Cache-Control'] = 'no-cache'
        bottle.response.status = 500

        json.dumps({
            'status':  'error',
            'message': 'Internal Server Error',
            'code':    500
        })


if __name__ == '__main__':
    start_api()
