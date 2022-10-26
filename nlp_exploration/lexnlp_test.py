import json

from lexnlp.extract.en import acts, amounts, dates, durations, money, percents
from lexnlp.nlp.en import tokens

f = open("judgement/judgements.json", "r")

judgements = json.load(f)

f.close()

for key in judgements.keys():
    for k, v in judgements[key].items():
        text = "\n".join(v)
        # """Pattern-based extraction"""
        print(list(amounts.get_amounts(text)))
        print(acts.get_act_list(text))
        print(list(dates.get_dates(text)))
        print(list(durations.get_durations(text)))
        print(list(money.get_money(text)))
        print(list(percents.get_percents(text)))
        # print(list(geoentities.get_geoentities(text, _CONFIG)))

        """Tokenization"""
        print(list(tokens.get_nouns(text)))
        print(list(tokens.get_verbs(text, lemmatize=True)))
        print(list(tokens.get_adjectives(text)))
        print(list(tokens.get_adverbs(text)))
        print()
