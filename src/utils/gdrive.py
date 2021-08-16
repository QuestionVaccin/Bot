from uuid import UUID

import gspread
from .creds_gdrive import CREDS
import os

PRODUCTION = os.getenv('PRODUCTION_VACCIN_INFO', 'false') == 'true'

scopes = ['https://www.googleapis.com/auth/spreadsheets']


class DoctorSheet(object):
    def __init__(self):
        gc = gspread.service_account_from_dict(CREDS)
        self.sheet = gc.open('Liste specialistes Bot').get_worksheet(0)
        self.tickets = gc.open('Liste specialistes Bot').get_worksheet(2)

    def get_list_doctors_active(self):
        """
        Return the doctor that are active in the gDrive spreadsheets
        :return:
        :rtype: list
        """
        docs = [doc[1:] for doc in self.sheet.col_values(1)[1:]]
        active = self.sheet.col_values(2)[1:]
        return [(d, a) for (d, a) in zip(docs, active)]

    def get_list_doctors(self):
        """
        Return the doctor that are active in the gDrive spreadsheets
        :return:
        :rtype: list
        """
        return [doc[1:] for doc in self.sheet.col_values(1)[1:]]

    def update_is_active(self, doctor_name: str, active: bool):
        """
        Update doctor activity on sheet
            - active: The doctor can be calle by the bot
            - not active: The doctor wont be call by the bot
        :return:
        :rtype: list
        """
        docs = [doc[1:] for doc in self.sheet.col_values(1)[1:]]
        index_in_sheet = next(index for d, index in zip(docs, list(range(len(docs)))) if d == doctor_name) + 2
        value = 'TRUE' if active is True else 'FALSE'
        self.sheet.update_cell(index_in_sheet, 2, value)

    def get_list_experts(self):
        if PRODUCTION:
            list_experts = self.get_list_doctors_active()
        else:
            list_experts = [ ('KillianGardabas', 'TRUE'), ('bernard_erwan', 'TRUE')]
        return list_experts

    def create_ticket(self, id: str, sender_id: str, date: str, ticket: UUID, question: str, specialist: str):
        val = [id, sender_id, date, ticket.__str__(), question, specialist]
        self.tickets.append_row(val)


if __name__ == "__main__":
    d = DoctorSheet()
    # print(d.get_list_doctors())
    d.update_is_active('CedricBrice', True)
