from uuid import UUID

import tweepy
import os
import pprint
import json

PRODUCTION = os.getenv('PRODUCTION_VACCIN_INFO', 'false') == 'true'

CONSUMER_API_KEY = os.environ.get('VACCIN_CONSUMER_API_KEY')
CONSUMER_API_SECRET = os.environ.get('VACCIN_CONSUMER_API_SECRET')
ACCESS_API_KEY = os.environ.get('VACCIN_ACCESS_API_KEY')
ACCESS_API_SECRET = os.environ.get('VACCIN_ACCESS_API_SECRET')

auth = tweepy.OAuthHandler(CONSUMER_API_KEY, CONSUMER_API_SECRET)
auth.set_access_token(ACCESS_API_KEY, ACCESS_API_SECRET)
pprint = pprint.PrettyPrinter()


class Twitter(object):
    last_message_treated_file: str = os.getenv('VACCIN_LAST_MESSAGE_TREATED_FILE',
                                               './24hours_messages_treated.json')

    def __init__(self):
        self.api = tweepy.API(auth)

    def get_me(self):
        return self.api.me()

    def can_send_private_message(self, sender_id, target_id):
        # Show friendship return a tuple with first -> source (The one how will send a message first)
        # and we return if the bot can dm the target
        return self.api.show_friendship(source_id=sender_id, target_id=target_id)[0].can_dm

    def get_last_day_tweets(self):
        with open(self.last_message_treated_file, 'r+') as f:
            list_tweets = json.loads(f.read())

        return list_tweets

    def get_last_private_message(self):
        """
        List direct message and save where we stop. And return any new element
        :return:
        :rtype:
        """
        return self.api.list_direct_messages()

    def get_user(self, **kwargs):
        if CONSUMER_API_SECRET and CONSUMER_API_KEY and ACCESS_API_SECRET and ACCESS_API_KEY:
            return self.api.get_user(kwargs)

    def get_username_from_id(self, id):
        if CONSUMER_API_SECRET and CONSUMER_API_KEY and ACCESS_API_SECRET and ACCESS_API_KEY:
            return self.api.get_user(id=id).screen_name

    def get_id_from_username(self, username):
        if CONSUMER_API_SECRET and CONSUMER_API_KEY and ACCESS_API_SECRET and ACCESS_API_KEY:
            return self.api.get_user(screen_name=username).id

    def send_private_message(self, message, user_id=None):
        if not PRODUCTION:
            print(f'---- response to {user_id} ---')
            print(message)

        if CONSUMER_API_SECRET and CONSUMER_API_KEY and ACCESS_API_SECRET and ACCESS_API_KEY:
            self.api.send_direct_message(recipient_id=user_id, text=message)

    def get_users(self, list_user_names=None, list_user_ids=None):
        if CONSUMER_API_SECRET and CONSUMER_API_KEY and ACCESS_API_SECRET and ACCESS_API_KEY:
            return self.api.lookup_users(user_ids=list_user_ids, screen_names=list_user_names)
        return []

    def send_private_message_with_redirection(self, message: str, user_id: str, user_redirect_id: str, ticket: UUID):
        if not PRODUCTION:
            print(f'---- send message with redirection for {user_id} ---')
            print(message)

        if CONSUMER_API_SECRET and CONSUMER_API_KEY and ACCESS_API_SECRET and ACCESS_API_KEY:
            self.api._send_direct_message(json_payload={'event': {
                'type': 'message_create',
                'message_create': {
                    'target': {'recipient_id': user_id},
                    'message_data': {
                        'text': message,
                        'ctas': [{
                            'type': 'web_url',
                            'label': "Envoyer un message",
                            'url': f'http://questionvaccin.e-bernard.me:5000/close_ticket?ticket_uuid={ticket.__str__()}'
                        }]
                    }
                }
            }})
