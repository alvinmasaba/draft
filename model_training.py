import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pickle

df = pd.read_csv("./data/database/training/training_data.csv")

selected_features = ['draft_age', 'ws', 'per', 'ortg', 'fta', 'ppg', 'fgm', 'trb', 'ts%', 'stl', 'drtg', 'ast', 'min', 'blk', 'tov', 'usg%']

X = df[selected_features]
y = df['Composite Success Score']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=52)

model = xgb.XGBRegressor(n_estimators=400, learning_rate=0.01, max_depth=4, random_state=52)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("Mean Squared Error: ", mse)
print("R2 Score: ", r2)

with open('./prediction_models/xgboost_model.pkl', 'wb') as file:
    pickle.dump(model, file)
