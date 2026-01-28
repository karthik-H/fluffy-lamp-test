"""
Entrypoint for fetching and preparing user data from JSONPlaceholder API.
"""

import logging
from services.user_service import UserService

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    logger = logging.getLogger(__name__)

    logger.info("Starting user data fetch from JSONPlaceholder API...")
    user_service = UserService()
    users = user_service.get_all_users()
    logger.info("Fetched %d users.", len(users))

    # Prepare data for further processing (here, just print summary)
    for user in users:
        logger.info(
            "User: id=%d, name=%s, username=%s, email=%s, phone=%s, website=%s",
            user.id, user.name, user.username, user.email, user.phone, user.website
        )

if __name__ == "__main__":
    main()