import pickle
import pandas as pd

with open('./prediction_models/xgboost_model.pkl', 'rb') as file:
    loaded_model = pickle.load(file)

# df = pd.read_csv("./data/database/test/testing_data.csv")
df = pd.read_csv("./data/database/clean/cleaned_prospect_data.csv")

selected_features = ['draft_age', 'ws', 'per', 'ortg', 'fta', 'ppg', 'fgm', 'trb', 'ts%', 'stl', 'drtg', 'ast', 'min', 'blk', 'tov', 'usg%']

new_data = df[selected_features]

df['Predicted Success Score'] = loaded_model.predict(new_data)
df = df[['name', 'Predicted Success Score']].sort_values(by='Predicted Success Score', ascending=False)
df.to_csv("./data/database/predictions/prospect_predictions.csv", index=False)
