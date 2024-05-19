import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import RFECV
from sklearn.model_selection import KFold

# Import the cleaned and processed DataFrame
df = pd.read_csv("./data/database/clean/cleaned_player_data.csv")

df_filtered = df[(df['ncaa_data_complete'] == True)]

# Define success indicators
success_indicators = [
    'nba_seasons', 'Player Of The Month', 'Wilt Chamberlain Rookie Of The Year',
    'all_star_selections', 'All-NBA First Team', 'All-NBA Second Team',
    'All-NBA Third Team','All-NBA Defensive First Team', 'All-NBA Defensive Second Team',
    'Michael Jordan Most Valuable Player', 'Hakeem Olajuwon Defensive Player Of The Year', 
    'All-Rookie First Team', 'All-Rookie Second Team', 'Career Average PER', 'Career Average PPG', 
    'Career Average WS','Career Average ORTG', 'Career Average DRTG',
    'Career Average MIN', 'Career Average TRB', 'Career Average AST', 'Career Average TS%',
    'Career Games Started', 'Career Total Points'
]

feature_columns = ['draft_age', 'ws', 'per', 'ortg', 'fta',
                   'ppg', 'fgm', 'trb', 'ts%', 'stl',
                  'drtg', 'trb', 'ftm', 'pf',
                  'min', 'blk', 'tov', 'usg%', 'height', 'weight'
                ]

# Normalize the success indicators using min-max normalization
scaler = MinMaxScaler()
normalized_success_indicators = scaler.fit_transform(df_filtered[success_indicators])

# Assign weights to the success indicators
weights = [0.05, 0.005, 0.07, 0.05, 0.10, 0.09, 0.05, 0.04, 0.03, 0.12, 0.05, 0.01, 
           0.005, 0.04, 0.04, 0.05, 0.025, 0.025, 0.02, 0.02, 0.02, 0.03, 
           0.03, 0.03]

# Calculate the composite success score
composite_success_score = (normalized_success_indicators * weights).sum(axis=1)
df_filtered['Composite Success Score'] = composite_success_score

# Define features and target variable
X = df_filtered[feature_columns]
y = df_filtered['Composite Success Score']

# Perform RFE with cross-validation
estimator = LinearRegression()
cv = KFold(n_splits=5, random_state=1, shuffle=True)
selector = RFECV(estimator, step=1, cv=cv, scoring='r2')
selector = selector.fit(X, y)

# Get the selected features
selected_features = X.columns[selector.support_]

print("Selected features:", selected_features)

# Save the training data
df_filtered.to_csv("./data/database/training/training_data.csv", index=False)