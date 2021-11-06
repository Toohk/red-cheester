# -*- coding: utf-8 -*-
import json

f = open("question.txt", "r", encoding='utf8')
txt = f.read()

data = {
    "questions" : []
}

x = txt.replace("</div>", "")
x = x.split("<div class='show-question'><div class='show-question-content'>")

del x[0]

id = 0

for q2 in x :

    q1 = q2.split("<ul>")
    id = id+1
    question = {
        "id" : id,
        "question" : "string",
        "difficulty" : 1,
        "answers" : []
    }
    question["question"] = q1[0]
    print(u""+q1[0])
    a = q1[1].split("</span></li>")
    del a[-1]

    for i in a:
        q = i.replace("</ul><p class='explanation'></p>", "")
        q = q = q.replace("<li class='answer'>", "")
        q = q = q.replace("<span class='answer'>", "")
        q = q = q.replace("<li class='answer user-answer'>", "")
        if "correct-answer" in q :
            q = q = q.replace("<li class='answer correct-answer'>", "")
            q = q = q.replace("<li class='answer user-answer correct-answer'>", "")
            question["answers"].append({
                "text" : q,
                "correct" : True
            })
        else : 
            question["answers"].append({
                    "text" : q,
                    "correct" : False
                })
    data["questions"].append(question)

with open('questions.json', 'w') as outfile:
    json.dump(data, outfile)




