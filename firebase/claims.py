if __name__ == "__main__":
    import os, sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
from typing import cast, Iterable
import json
from firebase_admin import credentials, auth, initialize_app
from __init__ import config


def list_users():
    for user in cast(Iterable[auth.UserRecord], auth.list_users().iterate_all()):
        print(f"User: {user.uid} has {json.dumps(user.custom_claims, indent=4)}")


if __name__ == "__main__":
    cred = credentials.Certificate(config.FIREBASE_ADMIN)
    initialize_app(cred)
    # uid = "sDadHAPRUvW4MCHAfO46L8RwUE23"
    # auth.set_custom_user_claims(uid, {"role": "tester"})
    list_users()
