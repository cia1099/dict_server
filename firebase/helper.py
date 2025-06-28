import asyncio
from datetime import datetime
from typing import cast, Iterable
from firebase_admin import credentials, auth, initialize_app, _apps
from router.remote_db import clear_user

EXTRA_GAS = 200.0


def clear_expirations(cred: credentials.Certificate):
    if not _apps:
        initialize_app(cred)
    ghosts: list[auth.UserRecord] = []
    now = round(datetime.now().timestamp())
    page = auth.list_users()
    while page:
        for user in cast(Iterable[auth.UserRecord], page.users):
            if len(user.provider_data) == 0 or not user.email_verified:
                metadata = user.user_metadata
                expire = now - (metadata.creation_timestamp or 0) // 1000
                if expire > 1440 * 60:
                    ghosts.append(user)
            else:
                claims = user.custom_claims or {}
                disabled_at = claims.get("disabled_at")
                if disabled_at:
                    time = datetime.strptime(disabled_at, "%Y-%m-%dT%H:%M:%SZ")
                    expire = now - int(time.timestamp())
                    if expire > 1440 * 60 * 7:
                        asyncio.run(clear_user(user.uid or ""))
                        ghosts.append(user)
                if claims.get("role") == "premium":
                    claims.update({"gas": EXTRA_GAS})
                    auth.set_custom_user_claims(user.uid, claims)
        page = page.get_next_page()
    # for user in ghosts:
    #     print(f"User: {user.uid} has {json.dumps(user._data, indent=4)}")
    ret = auth.delete_users([ghost.uid for ghost in ghosts])
    # TODO: replace print to log
    print("Successfully deleted {0} users".format(ret.success_count))
    print("Failed to delete {0} users".format(ret.failure_count))
    for err in ret.errors:
        print("error #{0}, reason: {1}".format(ret.index, ret.reason))
