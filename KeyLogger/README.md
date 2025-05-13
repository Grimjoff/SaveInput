# Unique Fingerprint
Educational purposes only, doing this for my private research without any evil intent.
This little projects goal is to create a sort of "unique Fingerprint"
for every user. This is done by tracking your keyboard inputs (Currently just in the discord application)
and saving them with a timestamp for when it was pressed and when it was released.
From that it derives the time it was held, groups the buttons together and creates a profile for that user.
Once enough data is collected there's a jupyter notebook where a model is trained.
The XGBoost tries to predict who wrote a specific message by analyzing previous messages written.
Since its hard to get people to install something that at its Core is a Keylogger, we create fake profiles for now. Currently they aren't that good so 
The Model struggles at predicting them right. The real user, which is currently only me, gets predicted very well, however that might be related to the model not seeing any pattern 
in the models at all.
Main started to be in python. However, due to needing real users to try this it was rewritten into C
so that others could execute it without needing a python interpreter.