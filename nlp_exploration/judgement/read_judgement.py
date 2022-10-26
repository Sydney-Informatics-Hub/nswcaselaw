# from tika import parser

# raw = parser.from_file('Hirachand-v-Hirachand.pdf')

# print(raw['content'].split("Lady Justice King:")[1])

import json

f = open("judgements.txt", "r")

judgements = [j.strip("\n") for j in f.readlines()]

f.close()

tidied = []
new_string = ""
for s in judgements:
    if s != "" and s != " ":
        new_string += s
    else:
        if new_string != "":
            tidied.append(new_string)
        new_string = ""

"""
{Title:
    {number: [text, text], number: [text], number: [text, text, text]},
title: {...}
}
# """

# for s in tidied:
#     print(s)
#     print("-------------------------------------------------------")


final_judgements = {}

i = 0
expected = 1
title = None
while i < len(tidied):
    if tidied[i][0].isupper() and tidied[i + 1].startswith(str(expected) + "."):
        title = tidied[i]
        if title not in final_judgements.keys():
            final_judgements[title] = {}
    elif tidied[i].startswith(str(expected) + "."):
        final_judgements[title][expected] = [tidied[i][2:].lstrip(". ")]
        expected += 1
    else:
        final_judgements[title][expected - 1].append(tidied[i])
    i += 1


print(json.dumps(final_judgements, indent=4))
