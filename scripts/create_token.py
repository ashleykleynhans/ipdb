from bottlejwt import JwtPlugin
import configparser


def validation(auth, auth_value):
    """Validate the JWT Authentication"""
    print(auth, auth_value)
    return True


# Initialise Config File
cfg = configparser.RawConfigParser()
cfg.read('.env')

# Get API Configuration
API_PASSWORD = cfg.get('api', 'API_PASS')

# is a singleton, you only need to initialize once.
# * If you did install () also work
JwtPlugin(validation, API_PASSWORD, algorithm='HS256')

print(JwtPlugin.encode({'username': 'ansible'}))
