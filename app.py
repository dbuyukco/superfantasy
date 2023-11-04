from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
# Fetch user's teams
sc = OAuth2(None, None, from_file='oauth2.json')
##Fantasy League 2023-2024 ID
league_id = '428.l.17054'
##Access token check.
if not sc.token_is_valid():
    sc.refresh_access_token()

# Fetch teams in the league
url_teams_in_league = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_id}/teams"
response_teams = sc.session.get(url_teams_in_league, params={'format': 'json'})
data_teams = response_teams.json()


lg = yfa.league.League(sc, league_id)
teams = yfa.league.League(sc, league_id).teams()
teams_list = {}
weeks_list = []
for team_key in teams:
    print(team_key)
    teams_list[teams[team_key]['name']] = team_key

for i in range(1, lg.current_week() + 1):
    weeks_list.append("Week " + str(i))
print(lg.end_week())
# Step 4: Parse and print the team names
st.sidebar.title("NBA Super Fantazi")
#matchups['fantasy_content']['league'][1]['scoreboard']['0']['matchups']['0']['matchup']['0']['teams']['0']['team']
# Sidebar Dropdown

team_options = list(teams_list.keys())
team_select = st.sidebar.selectbox("Select a team",team_options)

week_options = weeks_list
week_select = st.sidebar.selectbox("Select a week", week_options)

mode_options = ["Alternate Universe", "Mini Skirt Championship"]
mode_select = st.sidebar.selectbox("Select mode", mode_options)


# Fetch matchup data using the team key and week number
#url_matchup = f"https://fantasysports.yahooapis.com/fantasy/v2/team/428.l.17054.t.15/matchups;week=2"
#response_matchup = sc.session.get(url_matchup, params={'format': 'json'})
#week_matchup_for_team = response_matchup.json()

week_team_stats = pd.DataFrame(columns=['Team_Name', 'FG', 'FT', 'threePtm', 'Points', 'Rebound', 'Assists', 'Steal', 'Block', 'To', 'Is_Major'],index=range(16))
cross_points_df = pd.DataFrame(columns=['Team_Name', 'Score', 'FG', 'FT', 'threePtm', 'Points', 'Rebound', 'Assists', 'Steal', 'Block', 'To'], index=range(16))
cross_color_df = pd.DataFrame(columns=['Team_Name', 'Score', 'FG', 'FT', 'threePtm', 'Points', 'Rebound', 'Assists', 'Steal', 'Block', 'To'], index=range(16))

def get_team_stats(team_name):
    major_team_key = teams_list[team_name]
    matchup_list_selector = ['0','1','2','3','4','5','6','7']
    team_switch = ['0','1']
    idx = 0
    for select in matchup_list_selector:
        for switch in team_switch:
            key = week_matchups[select]['matchup']['0']['teams'][switch]['team'][0][0]['team_key']
            if key == major_team_key:
                week_team_stats.loc[idx].Is_Major = True
            else:
                week_team_stats.loc[idx].Is_Major = False
            week_team_stats.loc[idx].Team_Name = week_matchups[select]['matchup']['0']['teams'][switch]['team'][0][2]['name']
            fg = week_matchups[select]['matchup']['0']['teams'][switch]['team'][1]['team_stats']['stats'][0]['stat'][
                    'value']
            fg = fg.split('/')
            fg = float(int(fg[0]) / int(fg[1]))
            week_team_stats.loc[idx].FG = fg
            ft = week_matchups[select]['matchup']['0']['teams'][switch]['team'][1]['team_stats']['stats'][2]['stat'][
                    'value']
            ft = ft.split('/')
            ft = float(int(ft[0]) / int(ft[1]))
            week_team_stats.loc[idx].FT = ft
            week_team_stats.loc[idx].threePtm = int(week_matchups[select]['matchup']['0']['teams'][switch]['team'][1]['team_stats']['stats'][4]['stat'][
                    'value'])
            week_team_stats.loc[idx].Points = int(week_matchups[select]['matchup']['0']['teams'][switch]['team'][1]['team_stats']['stats'][5]['stat'][
                    'value'])
            week_team_stats.loc[idx].Rebound = int(week_matchups[select]['matchup']['0']['teams'][switch]['team'][1]['team_stats']['stats'][6]['stat'][
                    'value'])
            week_team_stats.loc[idx].Assists = int(week_matchups[select]['matchup']['0']['teams'][switch]['team'][1]['team_stats']['stats'][7]['stat'][
                    'value'])
            week_team_stats.loc[idx].Steal = int(week_matchups[select]['matchup']['0']['teams'][switch]['team'][1]['team_stats']['stats'][8]['stat'][
                    'value'])
            week_team_stats.loc[idx].Block = int(week_matchups[select]['matchup']['0']['teams'][switch]['team'][1]['team_stats']['stats'][9]['stat'][
                    'value'])
            week_team_stats.loc[idx].To = int(week_matchups[select]['matchup']['0']['teams'][switch]['team'][1]['team_stats']['stats'][10]['stat'][
                    'value'])
            idx += 1

    return week_team_stats


def calculate_weekly_score(t1,t2,idx):
    t1 = pd.DataFrame(t1).reset_index(drop=True)
    t2 = pd.DataFrame(t2).transpose().reset_index(drop=True)
    global cross_color_df
    t1 = t1.drop(columns=['Team_Name','Is_Major'])
    t2 = t2.drop(columns=['Team_Name','Is_Major'])
    win=0
    lose=0
    tie=0

    for column in t1.columns:
        if t1[column][0] > t2[column][0]:
            win += 1
            cross_color_df[column].loc[idx] = "Win"
        elif t1[column][0] < t2[column][0]:
            lose += 1
            cross_color_df[column].loc[idx] = "Lose"
        else:
            tie += 1
            cross_color_df[column].loc[idx] = "Tie"
    return str(win) + "-" + str(lose) + "-" + str(tie)



def get_cross_map():
    global cross_points_df
    global cross_color_df
    global week_team_stats
    major_df = week_team_stats.loc[week_team_stats['Is_Major'] == True]
    major_df = major_df.reset_index(drop=True)


    cross_points_df.loc[0].Team_Name = major_df['Team_Name'][0]
    cross_points_df.loc[0].Score = "-"
    cross_points_df.loc[0].FG = format(major_df['FG'][0], '.3f')
    cross_points_df.loc[0].FT = format(major_df['FT'][0], '.3f')
    cross_points_df.loc[0].threePtm = major_df['threePtm'][0]
    cross_points_df.loc[0].Points = major_df['Points'][0]
    cross_points_df.loc[0].Rebound = major_df['Rebound'][0]
    cross_points_df.loc[0].Assists = major_df['Assists'][0]
    cross_points_df.loc[0].Steal = major_df['Steal'][0]
    cross_points_df.loc[0].Block = major_df['Block'][0]
    cross_points_df.loc[0].To = major_df['To'][0]


    idx =1
    for index, row in week_team_stats.iterrows():
        if row['Is_Major'] == False:
            cross_points_df.loc[idx].Team_Name = row['Team_Name']
            cross_points_df.loc[idx].Score = calculate_weekly_score(major_df, row, idx)
            cross_points_df.loc[idx].FG = format(row['FG'], '.3f')
            cross_points_df.loc[idx].FT = format(row['FT'], '.3f')
            cross_points_df.loc[idx].threePtm = row['threePtm']
            cross_points_df.loc[idx].Points = row['Points']
            cross_points_df.loc[idx].Rebound = row['Rebound']
            cross_points_df.loc[idx].Assists = row['Assists']
            cross_points_df.loc[idx].Steal = row['Steal']
            cross_points_df.loc[idx].Block = row['Block']
            cross_points_df.loc[idx].To = row['To']
            idx += 1

    cross_color_df.fillna("None", inplace=True)
    print(1)


def highlight_cells(val, bool_val):
    if bool_val == "None":
        return 'background-color: green'
    elif bool_val == "Win":
        return 'background-color: green'
    elif bool_val == "Lose":
        return 'background-color: red'
    else:
        return 'background-color: yellow'


matchups = lg.matchups(week=week_select.split(' ')[1])
week_matchups = matchups['fantasy_content']['league'][1]['scoreboard']['0']['matchups']
weekly_team_stats = get_team_stats("Ergani Kakos")
get_cross_map()

color_map = {
    'Win': '#006400',
    'Lose': '#800000',
    'Tie': '#9ACD32',
    'None': '#0E1117'
}

df_color_codes = cross_color_df.applymap(color_map.get)

def apply_color(dataframe, colors):
    styled_df = pd.DataFrame('', index=dataframe.index, columns=dataframe.columns)
    for row in styled_df.index:
        for col in styled_df.columns:
            styled_df.at[row, col] = f'background-color: {colors.at[row, col]}'
    return styled_df

cross_points_df = cross_points_df.style.apply(apply_color, colors=df_color_codes, axis=None)


#styles = pd.DataFrame('', index=cross_points_df.index, columns=cross_points_df.columns)

#cross_points_df = cross_points_df.style.applymap(highlight_cells, bool_val=cross_color_df)
#st.write(cross_points_df)
st.dataframe(cross_points_df, height=600, use_container_width=True)

if mode_select == "Alternate Universe":
    matchups = lg.matchups(week=week_select.split(' ')[1])
    week_matchups = matchups['fantasy_content']['league'][1]['scoreboard']['0']['matchups']
    print(1)
    print(1)

elif mode_select == "Mini Skirt Championship":
    print(2)