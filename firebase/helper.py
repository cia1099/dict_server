from datetime import datetime
from typing import cast, Iterable
from firebase_admin import credentials, auth, initialize_app, _apps


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
    # for user in ghosts:
    #     print(f"User: {user.uid} has {json.dumps(user._data, indent=4)}")
    ret = auth.delete_users([ghost.uid for ghost in ghosts])
    # TODO: replace print to log
    print("Successfully deleted {0} users".format(ret.success_count))
    print("Failed to delete {0} users".format(ret.failure_count))
    for err in ret.errors:
        print("error #{0}, reason: {1}".format(ret.index, ret.reason))
