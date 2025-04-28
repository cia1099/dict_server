if __name__ == "__main__":
    import os, sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
from typing import cast, Iterable
import json, time
from datetime import datetime
from multiprocessing import Process
from firebase_admin import credentials, auth, initialize_app, _apps
from __init__ import config


def list_users(cred: credentials.Certificate):
    if not _apps:
        initialize_app(cred)
    for user in cast(Iterable[auth.UserRecord], auth.list_users().iterate_all()):
        print(f"User: {user.uid} has {json.dumps(user._data, indent=4)}")
        # print(f"User: {user.uid} has {json.dumps(user.user_metadata, indent=4)}")
        # provider: fa.ProviderUserInfo = user.provider_data[0]
        # print(f"User: {user.uid} has {user.provider_data}")


def clear_expirations(cred: credentials.Certificate):
    if not _apps:
        initialize_app(cred)
    ghosts: list[auth.UserRecord] = []
    now = int(datetime.now().timestamp() * 1e3)
    page = auth.list_users()
    while page:
        for user in cast(Iterable[auth.UserRecord], page.users):
            if len(user.provider_data) == 0 or not user.email_verified:
                metadata = user.user_metadata
                expire = now - (metadata.creation_timestamp or 0)
                if expire > 1440 * 60:
                    ghosts.append(user)
        page = page.get_next_page()
    for user in ghosts:
        print(f"User: {user.uid} has {json.dumps(user._data, indent=4)}")


if __name__ == "__main__":
    cred = credentials.Certificate(config.FIREBASE_ADMIN)
    app = initialize_app(cred)
    uid = "kFIiU336lxQjtwSIiPyTA32boPt2"
    user: auth.UserRecord = auth.get_user(uid)
    claims = user.custom_claims or {}
    # claims.update({"extra": 200.0})
    # auth.set_custom_user_claims(uid, claims)
    # print(user.custom_claims)
    list_users(cred)
    # p = Process(target=clear_expirations, args=(cred,))
    # p.daemon = False
    # p.start()

    print("terminal main process")
