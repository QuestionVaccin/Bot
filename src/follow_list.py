import tweepy
import os
import pprint

from utils.twitter import Twitter

PRODUCTION = os.getenv('PRODUCTION_VACCIN_INFO', 'false') == 'true'

CONSUMER_API_KEY = os.environ.get('VACCIN_CONSUMER_API_KEY')
CONSUMER_API_SECRET = os.environ.get('VACCIN_CONSUMER_API_SECRET')
ACCESS_API_KEY = os.environ.get('VACCIN_ACCESS_API_KEY')
ACCESS_API_SECRET = os.environ.get('VACCIN_ACCESS_API_SECRET')

auth = tweepy.OAuthHandler(CONSUMER_API_KEY, CONSUMER_API_SECRET)
auth.set_access_token(ACCESS_API_KEY, ACCESS_API_SECRET)
pprint = pprint.PrettyPrinter()

list_to_follow = ["NyctaDoc",
                  "PCHARBONNEL01",
                  "Sonic_urticant",
                  "AlexSamTG",
                  "GuisonJerome",
                  "Gothgoth_",
                  "DIntubator",
                  "Slaanor",
                  "CedricBrice",
                  "spolochon",
                  "UDOWave",
                  "Kejaan_DeBelaan",
                  "namyolivier",
                  "buckd949",
                  "drmadur",
                  "StefPMaz",
                  "biologyar",
                  "bouletedebijou",
                  "MarieDAdC",
                  "coraly_n",
                  "joulaudl",
                  "MedecinDesAbers",
                  "serre_pat",
                  "pallia_doc",
                  "maman_poissons",
                  "Sarah_E_56",
                  "Juceinthebox",
                  "Droliv81",
                  "OliveYorffegson",
                  "AllHallowsEve6",
                  "AudeSirven",
                  "Patricia_Durand",
                  "_MarcGielen_",
                  "pabonnet",
                  # "SophieDischeune",
                  "lambteam44",
                  "panarmorix",
                  "MalachiPilgrimC",
                  "DocPepper_FR",
                  "SPilleron",
                  "galigali07"]


if __name__ == "__main__":
    if CONSUMER_API_SECRET and CONSUMER_API_KEY and ACCESS_API_SECRET and ACCESS_API_KEY:
        api = tweepy.API(auth)
        twitter = Twitter
        user_already_followed = [elem.lower() for elem in twitter.get_expert_from_following()]
        print(user_already_followed)
        for elem in list_to_follow:
            if elem.lower() not in user_already_followed:
                print(elem)
                try:
                  api.create_friendship(screen_name=elem)
                except Exception:
                    print(f"{elem} do not exist")
