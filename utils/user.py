import json

FILE_USERS_PATH = './utils/users.json'


def getUsers():
    names = []
    usernames = []
    passwords = []

    with open(FILE_USERS_PATH, 'r') as j:
        contents = json.loads(j.read())
        for i in range(len(contents['data'])):
            names.append(contents['data'][i]['name'])
            usernames.append(contents['data'][i]['username'])
            passwords.append(contents['data'][i]['password'])
    return names, usernames, passwords
