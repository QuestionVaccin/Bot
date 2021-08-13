#! /bin/env python3
import pprint
import uuid

import sentry_sdk
import json

import os
from datetime import datetime, timedelta

from utils.twitter import Twitter
from utils.gdrive import DoctorSheet

os.environ['TZ'] = 'Europe/Paris'
now = datetime.now()
pprint = pprint.PrettyPrinter()
PRODUCTION = os.getenv('PRODUCTION_VACCIN_INFO', 'false') == 'true'

if PRODUCTION:
    sentry_sdk.init(
        "https://3d900e44eaa14af5965f2a28b94c758b@o938280.ingest.sentry.io/5888238",

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0
    )

MP_CLOSED = """Vos messages ne sont pas ouverts, ouvrez-les pour qu'un spécialiste puisse prendre contact avec vous\n
Plus > Paramètres et Confidentialité > Confidentialité et sécurité > Message privés > activer les demandes de message de tout le monde.
Puis renvoyez 'question'"""


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class VaccinInfo(object):
    last_message_file: str = os.getenv('VACCIN_LAST_MESSAGE_FILE', './last_message_read.txt')
    last_message_treated_file: str = os.getenv('VACCIN_LAST_MESSAGE_TREATED_FILE', './24hours_messages_treated.json')
    doctor_id_file: str = os.getenv('VACCIN_DOCTOR_ID_FILE', './doctor_id.txt')
    my_twitter_id: str
    list_experts: list
    last_days_tweets: list
    slow_mode_user: set

    def __init__(self):
        self.doctor_sheet = DoctorSheet()
        self.twitter = Twitter()
        self.already_send_id = []
        self.my_twitter_id = str(self.twitter.get_me().id)
        self.list_experts = self.doctor_sheet.get_list_experts()
        self.last_days_tweets = self.twitter.get_last_day_tweets()
        self.slow_mode_user = set([elem['message_create']['sender_id'] for elem in self.last_days_tweets])
        self.doctor_id = 0
        with open(self.doctor_id_file, 'r+') as f:
            self.doctor_id = int(f.read())
        self.tmp_doctor_id = self.doctor_id

        #all_doctor_name = [d[0] for d in self.list_experts]
        #all_doctor_users = []
        #for sublist in list(chunks(all_doctor_name, 100)):
            #all_doctor_users.append(self.twitter.get_users(list_user_names=sublist))


    def get_doctor(self):
        while True:
            if self.list_experts[self.doctor_id][1] == 'TRUE':
                return self.list_experts[self.doctor_id][0]

            self.next_doctor()

    def next_doctor(self):
        self.doctor_id += 1
        self.doctor_id = 0 if self.doctor_id >= len(self.list_experts) else self.doctor_id

    def anonymize_name(self, name: str):
        first_c = name[0]
        last_c = name[-1]
        return first_c \
            + ''.join(['*' for index in range(len(name)) if index != 0 and index != len(name) - 1]) \
            + last_c

    def forward_to_doctor_and_patient(self, message: str, doctor_id: str, sender_id: str, doctor_name: str, sender_name: str, ticket: uuid.UUID):
        doctor_name = self.anonymize_name(doctor_name)
        self.twitter.send_private_message_with_redirection(
            message=f"""@{sender_name} veut en savoir plus sur la vaccination.
{"Sa question: " + message if message.strip().lower() != 'question' else ""}


Prenez contact avec lui""",
            user_id=doctor_id,
            user_redirect_id=sender_id,
            ticket=ticket
        )
        self.twitter.send_private_message(f"""Bonjour
@ {doctor_name} va vous répondre dans les heures qui suivent, Restez connecté ! Vous pourrez alors poser vos questions sur la vaccination !
(Le message du spécialiste peut arriver dans "demande de message", en haut de votre messagerie twitter)""",
                                          user_id=sender_id)

    def ask_get_in_touch_with_a_doctor(self, elem):
        return (
                (elem.message_create['message_data'].get('quick_reply_response') is not None and
                 elem.message_create['message_data']['quick_reply_response']['metadata'] == 'prendre_contact') or
                elem.message_create['message_data']['text'].strip().lower() == 'question'
        )

    def chose_doc_for_message(self, elem, sender_name):
        patient_id = elem.message_create['sender_id']
        while True:
            doctor_name = self.get_doctor()
            doctor_id = self.twitter.get_id_from_username(doctor_name) # TODO can be optimize with one call to get all ids
            response = self.twitter.can_send_private_message(doctor_id, patient_id)

            if not response:
                self.twitter.send_private_message(MP_CLOSED, user_id=patient_id)
                break
            else:
                try:
                    ticket = uuid.uuid4()
                    self.next_doctor()
                    self.forward_to_doctor_and_patient(elem.message_create['message_data']['text'],
                                                       doctor_id, patient_id, doctor_name, sender_name, ticket)
                    self.already_send_id.append(elem.message_create['sender_id'])
                    self.last_days_tweets.append(elem._json)

                    created_at = datetime.fromtimestamp(int(elem.created_timestamp) / 1000).isoformat()
                    self.doctor_sheet.create_ticket(elem.id, created_at, ticket,
                                                    elem.message_create['message_data']['text'], doctor_name)
                    break
                except Exception as e:
                    print(e)

    def update_doctor_status(self, doctor_name, doctor_id, message):
        if message == 'help':
            self.twitter.send_private_message(
                """- Envoyez 'pause' pour arrêter de recevoir des messages

- Et 'unpause' pour les recevoir à nouveau""",
                doctor_id)
        elif message == 'pause':
            self.doctor_sheet.update_is_active(doctor_name, False)
            self.twitter.send_private_message(
                """Vous êtes désormais en pause""",
                doctor_id)
        elif message == 'unpause':
            self.twitter.send_private_message(
                """Vous êtes de nouveau actif""",
                doctor_id)
            self.doctor_sheet.update_is_active(doctor_name, True)
        else:
            self.twitter.send_private_message(
                """- Envoyez 'pause' pour arrêter de recevoir des messages

- Et 'unpause' pour les recevoir à nouveau""",
                doctor_id)

    def run(self):
        last_private_message = self.twitter.get_last_private_message()

        if not last_private_message:
            print('no messages returned')
            return

        most_recent_id = last_private_message[0].id
        with open(self.last_message_file, 'r+') as f:
            last_message_id = f.read()

        with open(self.last_message_file, 'w+') as f:
            f.write(most_recent_id)

        #all_sender_ids = [elem.message_create['sender_id'] for elem in last_private_message]
        #all_sender_users = []
        #for sublist in list(chunks(all_sender_ids, 100)):
         #   all_sender_users.append(self.twitter.get_users(list_user_ids=sublist))

        for elem in last_private_message:
            if elem.id == last_message_id:
                print('Message already processed loop stopped')
                break

            if elem.message_create['sender_id'] == self.my_twitter_id or \
                    elem.message_create['sender_id'] in self.already_send_id:
                continue

            print(elem.id)
            try:
                sender_id = elem.message_create['sender_id']
                sender_name = self.twitter.get_username_from_id(sender_id) # TODO can be optimize with one call to get all ids
                if sender_name in self.doctor_sheet.get_list_doctors():
                    self.update_doctor_status(sender_name, sender_id, elem.message_create['message_data']['text'].strip().lower())
                elif elem.message_create['sender_id'] not in self.slow_mode_user:
                    self.chose_doc_for_message(elem, sender_name)
                else:
                    print('antispam request')
            except Exception as e:
                print(f"Weird error appears with user: {sender_name}", e)

    def update_last_messages_treated(self, datas):
        with open(self.last_message_treated_file, 'w+') as f:
            f.write(json.dumps(datas))

    def __del__(self):
        save_tweets = []
        for elem in self.last_days_tweets:
            creation_date = datetime.fromtimestamp(int(elem['created_timestamp'])/1000)
            if datetime.now() - creation_date < timedelta(hours=20):
                save_tweets.append(elem)

        with open(self.doctor_id_file, 'w+') as f:
            f.truncate(0)
            f.write(str(self.doctor_id))
        self.update_last_messages_treated(save_tweets)


def main():
    bot = VaccinInfo()
    bot.run()


if __name__ == "__main__":
    print(f'--- start script {datetime.now()} ---')
    main()
    print(f'--- end script {datetime.now()} ---')
