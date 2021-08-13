import tweepy
from tweepy.binder import bind_api
import os

CONSUMER_API_KEY = os.environ.get('VACCIN_CONSUMER_API_KEY')
CONSUMER_API_SECRET = os.environ.get('VACCIN_CONSUMER_API_SECRET')
ACCESS_API_KEY = os.environ.get('VACCIN_ACCESS_API_KEY')
ACCESS_API_SECRET = os.environ.get('VACCIN_ACCESS_API_SECRET')

auth = tweepy.OAuthHandler(CONSUMER_API_KEY, CONSUMER_API_SECRET)
auth.set_access_token(ACCESS_API_KEY, ACCESS_API_SECRET)


def set_welcome_message():
    api = tweepy.API(auth)
    list_api_welcome_message = bind_api(api=api, path='/direct_messages/welcome_messages/list.json', method='GET',
                                       payload_type='direct_message', allowed_param=[], require_auth=True)
    l = list_api_welcome_message()._json
    if l and l["welcome_messages"].__len__():
        print(l)
        print(l["welcome_messages"][0]["id"])
        delete_api_welcome_message = bind_api(api=api, path=f'/direct_messages/welcome_messages/destroy.json?id={l["welcome_messages"][0]["id"]}',
                                              method='DELETE', payload_type='direct_message', allowed_param=[], require_auth=True)
        try:
            delete_api_welcome_message()
        except Exception:
            print('error')
        print(list_api_welcome_message()._json)
    new_api_welcome_message = bind_api(api=api, path='/direct_messages/welcome_messages/new.json', method='POST',
                                       payload_type='direct_message', allowed_param=[], require_auth=True)
    set_api_welcome_message = bind_api(api=api, path='/direct_messages/welcome_messages/rules/new.json', method='POST',
                                       payload_type='direct_message', allowed_param=[], require_auth=True)
    w = new_api_welcome_message(json_payload={
        "welcome_message": {
            "name": "simple_welcome-message 01",
            "message_data": {
                "text": """
Bienvenue!
Envoyez votre question pour être mis en contact avec un spécialiste. 
Vous pourrez alors lui poser directement votre question.
(Le bot et les spécialistes peuvent prendre du temps à vous répondre, un peu de patience)
""",
            }
        }
    })
    set_api_welcome_message(json_payload={
        'welcome_message_rule': {
            'welcome_message_id': w._json['welcome_message']['id'],
        }
    })


if __name__ == "__main__":
    print(set_welcome_message())
