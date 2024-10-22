from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
#import datetime

Gold_Medal = "🥇"
Silver_Medal = "🥈"
Bronze_Medal = "🥉"

st.set_page_config(layout="wide")

# Fetch user's teams
sc = OAuth2(None, None, from_file='oauth2.json')
##Fantasy League 2023-2024 ID
league_id = '428.l.17054'
image = open('logo.png', 'rb').read()
st.sidebar.image(image, caption='', width=100)

##Access token check.
if not sc.token_is_valid():
    sc.refresh_access_token()

lg = yfa.league.League(sc, league_id)
teams = yfa.league.League(sc, league_id).teams()

teams_list = {}
weeks_list = []
for team_key in teams:
    teams_list[teams[team_key]['name']] = team_key
for i in range(1, lg.current_week() + 1):
    weeks_list.append("Week " + str(i))

# Step 4: Parse and print the team names
st.sidebar.title("NBA Super Fantazi")

team_options = list(teams_list.keys())
team_select = st.sidebar.selectbox("Select a team",team_options)

mode_options = ["Alternate Universe", "Alternate Universe - Matchups", "Power Rankings", "Medal Board", "Box Plots", "Total Stats", "Team Info"]
mode_select = st.sidebar.selectbox("Select mode", mode_options)

if mode_select == "Box Plots":
    boxplot_sub_mode_options = ["Box - Weekly", "Box & SD - Weekly", "Box - Total"]
    sub_mode_select = st.sidebar.selectbox("Select submode", boxplot_sub_mode_options)
    if sub_mode_select == "Box - Weekly" or sub_mode_select == "Box & SD - Weekly":
        week_options = reversed(weeks_list)
        week_select = st.sidebar.selectbox("Select a week", week_options)
elif mode_select == "Team Info":
    boxplot_sub_mode_options = ["Profile", "Loyalty", "Healthy", "Story Mode"]
    sub_mode_select = st.sidebar.selectbox("Select submode", boxplot_sub_mode_options)

if mode_select == "Alternate Universe - Matchups":
    matchup_options = list(teams_list.keys())
    matchup_select = st.sidebar.selectbox("Select a matchup", matchup_options)
    cross_points_df = pd.DataFrame(columns=['Week','Team_Name', 'Score', 'FG', 'FT', 'threePtm', 'Points', 'Rebound', 'Assists', 'Steal', 'Block', 'To'], index=range(2))
    cross_color_df = pd.DataFrame(columns=['Week','Team_Name', 'Score', 'FG', 'FT', 'threePtm', 'Points', 'Rebound', 'Assists', 'Steal', 'Block', 'To'], index=range(2))
    cross_color_df.fillna("None", inplace=True)
else:
    if mode_select == "Alternate Universe" or mode_select == "Medal Board":
        week_options = reversed(weeks_list)
        week_select = st.sidebar.selectbox("Select a week", week_options)
    cross_points_df = pd.DataFrame(columns=['Team_Name', 'Score', 'FG', 'FT', 'threePtm', 'Points', 'Rebound', 'Assists', 'Steal', 'Block', 'To'], index=range(16)) 
    cross_color_df = pd.DataFrame(columns=['Team_Name', 'Score', 'FG', 'FT', 'threePtm', 'Points', 'Rebound', 'Assists', 'Steal', 'Block', 'To'], index=range(16))
    cross_color_df.fillna("None", inplace=True)

week_team_stats = pd.DataFrame(columns=['Team_Name', 'FGM', 'FGA', 'FG', 'FTM', 'FTA', 'FT', 'threePtm', 'Points', 'Rebound', 'Assists', 'Steal', 'Block', 'To', 'Is_Major'],index=range(16))
total_team_stats = pd.DataFrame(columns=['Team_Name', 'FGM', 'FGA', 'FG', 'FTM', 'FTA', 'FT', 'threePtm', 'Points', 'Rebound', 'Assists', 'Steal', 'Block', 'To', 'Is_Major'],index=range(16))

other_team = []

draft_res = lg.draft_results()
#draft_day = datetime.date(2023, 10, 22)
#start_day = datetime.date(2023, 10, 24)
#today = datetime.datetime.now()

def get_team_stats(team_name, major_bool = False):
    global other_team
    matchup_list_selector = ['0','1','2','3','4','5','6','7']
    team_switch = ['0','1']
    idx = 0
    for select in matchup_list_selector:
        for switch in team_switch:
            key = week_matchups[select]['matchup']['0']['teams'][switch]['team'][0][0]['team_key']
            if major_bool == True:
                major_team_key = teams_list[team_name]
                if key == major_team_key:
                    week_team_stats.loc[idx].Is_Major = True
                    other_team_idx = '1' if switch == '0' else '0'
                    other_team = week_matchups[select]['matchup']['0']['teams'][other_team_idx]['team'][0][2]['name']
                else:
                    week_team_stats.loc[idx].Is_Major = False
            else:
                week_team_stats.loc[idx].Is_Major = False
            week_team_stats.loc[idx].Team_Name = week_matchups[select]['matchup']['0']['teams'][switch]['team'][0][2]['name']

            fGfT = [0,2]
            count =0
            for p in fGfT:
                stat = week_matchups[select]['matchup']['0']['teams'][switch]['team'][1]['team_stats']['stats'][p]['stat']['value']
                stat = stat.split('/')
                if stat[0] == '': stat[0] = 0
                if stat[1] == '': stat[1] = 0
                week_team_stats.loc[idx].iloc[1+count*3] = int(stat[0])
                week_team_stats.loc[idx].iloc[2+count*3] = int(stat[1])
                try:
                    stat = float(int(stat[0]) / int(stat[1]))
                except:
                    stat = 0
                week_team_stats.loc[idx].iloc[3+count*3] = stat
                count += 1
                
            for s in range(4,11):
                stat = week_matchups[select]['matchup']['0']['teams'][switch]['team'][1]['team_stats']['stats'][s]['stat']['value']
                if stat == '': stat = 0
                week_team_stats.loc[idx].iloc[s+3] = int(stat)

            idx += 1

    return week_team_stats

def get_total_team_stats(team_name, major_bool = True):
    global week_matchups
    global total_team_stats
    global weekly_team_stats
    i=0
    for team in teams_list:
        total_team_stats.loc[i].Team_Name = team
        i += 1
    total_team_stats.fillna("0", inplace=True)

    for week in weeks_list:
        matchups = lg.matchups(week=week.split(' ')[1])
        week_matchups = matchups['fantasy_content']['league'][1]['scoreboard']['0']['matchups']
        weekly_team_stats = get_team_stats(team_select, major_bool=True)
        for index, row in weekly_team_stats.iterrows():
            for idx in range(0,16):
                if total_team_stats.loc[idx].Team_Name == row['Team_Name']:
                    total_team_stats.loc[idx].FGM = int(total_team_stats.loc[idx].FGM) + row['FGM']
                    total_team_stats.loc[idx].FGA = int(total_team_stats.loc[idx].FGA) + row['FGA']
                    total_team_stats.loc[idx].FTM = int(total_team_stats.loc[idx].FTM) + row['FTM']
                    total_team_stats.loc[idx].FTA = int(total_team_stats.loc[idx].FTA) + row['FTA']
                    total_team_stats.loc[idx].threePtm = int(total_team_stats.loc[idx].threePtm) + row['threePtm']
                    total_team_stats.loc[idx].Points = int(total_team_stats.loc[idx].Points) + row['Points']
                    total_team_stats.loc[idx].Rebound = int(total_team_stats.loc[idx].Rebound) + row['Rebound']
                    total_team_stats.loc[idx].Assists = int(total_team_stats.loc[idx].Assists) + row['Assists']
                    total_team_stats.loc[idx].Steal = int(total_team_stats.loc[idx].Steal) + row['Steal']
                    total_team_stats.loc[idx].Block = int(total_team_stats.loc[idx].Block) + row['Block']
                    total_team_stats.loc[idx].To = int(total_team_stats.loc[idx].To) + row['To']
                    total_team_stats.loc[idx].Is_Major = row['Is_Major']
                    break
    for idx in range(0,16):        
        total_team_stats.loc[idx].FG = format(total_team_stats.loc[idx].FGM / total_team_stats.loc[idx].FGA , '.3f')
        total_team_stats.loc[idx].FT = format(total_team_stats.loc[idx].FTM / total_team_stats.loc[idx].FTA , '.3f')
    
    return total_team_stats

def calculate_weekly_score(t1,t2,idx):
    t1 = pd.DataFrame(t1).reset_index(drop=True)
    t2 = pd.DataFrame(t2).transpose().reset_index(drop=True)
    global cross_color_df
    t1 = t1.drop(columns=['Team_Name','FGM','FGA','FTA','FTM','Is_Major'])
    t2 = t2.drop(columns=['Team_Name','FGM','FGA','FTA','FTM','Is_Major'])
    win=0
    lose=0
    tie=0

    for column in t1.columns:
        if column == 'To':
            if t1[column][0] < t2[column][0]:
                win += 1
                if idx == -1:
                    cross_color_df[column].loc[1] = "Win"
                else:
                    cross_color_df[column].loc[idx] = "Win"

            elif t1[column][0] > t2[column][0]:
                lose += 1
                if idx == -1:
                    cross_color_df[column].loc[1] = "Lose"
                else:
                    cross_color_df[column].loc[idx] = "Lose"
            else:
                tie += 1
                if idx == -1:
                    cross_color_df[column].loc[1] = "Tie"
                else:                
                    cross_color_df[column].loc[idx] = "Tie"
        else:
            if t1[column][0] > t2[column][0]:
                win += 1
                if idx == -1:
                    cross_color_df[column].loc[1] = "Win"
                else:                
                    cross_color_df[column].loc[idx] = "Win"
            elif t1[column][0] < t2[column][0]:
                lose += 1
                if idx == -1:
                    cross_color_df[column].loc[1] = "Lose"
                else:                
                    cross_color_df[column].loc[idx] = "Lose"
            else:
                tie += 1
                if idx == -1:
                    cross_color_df[column].loc[1] = "Tie"
                else:                
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
    return cross_points_df

def get_cross_map_matchup():

    global cross_points_df
    global cross_color_df
    global matchup_select
    global week_matchups

    for week in weeks_list:
        matchups = lg.matchups(week=week.split(' ')[1])
        week_matchups = matchups['fantasy_content']['league'][1]['scoreboard']['0']['matchups']
        weekly_team_stats = get_team_stats(team_select, major_bool = True)

        major_df = weekly_team_stats.loc[weekly_team_stats['Is_Major'] == True]
        major_df = major_df.reset_index(drop=True)

        cross_points_df.loc[0].Week = week
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
        
        for index, row in weekly_team_stats.iterrows():
            if row['Team_Name'] == matchup_select:
                cross_points_df.loc[1].Week = ""
                cross_points_df.loc[1].Team_Name = row['Team_Name']
                cross_points_df.loc[1].Score = calculate_weekly_score(major_df, row, -1)
                cross_points_df.loc[1].FG = format(row['FG'], '.3f')
                cross_points_df.loc[1].FT = format(row['FT'], '.3f')
                cross_points_df.loc[1].threePtm = row['threePtm']
                cross_points_df.loc[1].Points = row['Points']
                cross_points_df.loc[1].Rebound = row['Rebound']
                cross_points_df.loc[1].Assists = row['Assists']
                cross_points_df.loc[1].Steal = row['Steal']
                cross_points_df.loc[1].Block = row['Block']
                cross_points_df.loc[1].To = row['To']
        
        df_color_codes = cross_color_df.map(color_map.get)
        style_cross = cross_points_df.style.apply(apply_color, colors=df_color_codes, axis=None)
        st.dataframe(style_cross, height=109, use_container_width=True)
        
    return cross_points_df

def ewlt_get(cross_map):
    vals = cross_map.loc[1:].Score.tolist()
    ewlt = {}
    w,l,t = 0,0,0
    for wlt in vals:
        wlt = wlt.split('-')
        w = w + int(wlt[0])
        l = l + int(wlt[1])
        t = t + int(wlt[2])
    w = w / len(vals)
    l = l / len(vals)
    t = t / len(vals)
    ewlt['Win'] = w
    ewlt['Lose'] = l
    ewlt['Tie'] = t
    return ewlt

color_map = {
    'Win': '#006400',
    'Lose': '#800000',
    'Tie': '#9ACD32',
    'None': '#0E1117',
    'Match': "#00008B"
}

color_map_total = {
        'None': '#0E1117',
        'Match': "#00008B"
}

def update_other_team_color():
    global cross_color_df
    global cross_points_df
    global other_team

    idx = cross_points_df[cross_points_df['Team_Name'] == other_team].index
    cross_color_df.loc[idx, 'Team_Name'] = "Match"
    cross_color_df.loc[idx, 'Score'] = "Match"

def apply_color(dataframe, colors):
    styled_df = pd.DataFrame('', index=dataframe.index, columns=dataframe.columns)
    for row in styled_df.index:
        for col in styled_df.columns:
            styled_df.at[row, col] = f'background-color: {colors.at[row, col]}'
    return styled_df

def render_medal_board():
    global week_matchups
    week_matchups = lg.matchups(week=week_select.split(' ')[1])['fantasy_content']['league'][1]['scoreboard']['0']['matchups']
    weakly_leaderboard = get_team_stats(team_select, major_bool = True)

    #matchups = lg.matchups(week_select.split(' ')[1])['fantasy_content']['league'][1]['scoreboard']['0']['matchups']
    #print("Match count" + str(matchups['count']))
    #league_matchups_list = []
    #for i in range(matchups['count']):
    #    #display(pd.json_normalize(matchupss[m]['matchup']))
    #    #print(matchups[str(i)]['matchup']['0'])
    #    teams = matchups[str(i)]['matchup']['0']['teams']
    #    for t in range(teams['count']):
    #        val_list = []
    #        #print(teams[str(t)]['team'][0][2]) #team name
    #        team_data = [teams[str(t)]['team'][0][2]['name']]
    
    #       for s in teams[str(t)]['team'][1]['team_stats']['stats']:
    #            team_data.append(str(s['stat']['value']))

    #        league_matchups_list.append(team_data)

    #weakly_leaderboard=pd.DataFrame(league_matchups_list,columns=['TeamName','FG','FG%','FT','FT%','3Points','Points','Reb','Ast','St','Blk','To' ]).astype({'TeamName':'object','FG':'object','FG%':'float64','FT':'object','FT%':'float64','3Points':'int64','Points':'int64','Reb':'int64','Ast':'int64','St':'int64','Blk':'int64','To':'int64'})
    
    categories = ['threePtm','Points','Rebound','Assists','Steal','Block']
    
    for c in ['FG', 'FT']:
        temp = weakly_leaderboard.sort_values(c,ascending=False).reset_index(drop=True)
        #temp[c+' '] = temp[c].round(4).astype(str)
        temp[c+' ']  = temp[c].apply(lambda x: '{0:.3f}'.format(x))
        temp[c+' '][0] = "{:.3f}".format(temp[c][0]) + Gold_Medal
        temp[c+' '][1] = "{:.3f}".format(temp[c][0])  + Silver_Medal
        temp[c+' '][2] = "{:.3f}".format(temp[c][0])  + Bronze_Medal
        weakly_leaderboard = temp.replace(np.nan,'')

    for c in categories:
        temp = weakly_leaderboard.sort_values(c,ascending=False).reset_index(drop=True)
        temp[c+' '] = temp[c]
        temp[c+' '][0] = str(temp[c][0]) + Gold_Medal
        temp[c+' '][1] = str(temp[c][1]) + Silver_Medal
        temp[c+' '][2] = str(temp[c][2]) + Bronze_Medal
        weakly_leaderboard = temp.replace(np.nan,'')
    temp = weakly_leaderboard.sort_values('To',ascending=True).reset_index(drop=True)
    temp['To '] = temp['To']
    temp['To '][0] =  str(temp['To'][0]) + Gold_Medal
    temp['To '][1] =  str(temp['To'][1]) + Silver_Medal
    temp['To '][2] =  str(temp['To'][2]) + Bronze_Medal
    weakly_leaderboard = temp.replace(np.nan,'')
    
    Total_Medals = []
    Total_Medals_Count = []
    for i in range(len(weakly_leaderboard)):
        g_count=0
        s_count=0
        b_count = 0
        for index, value in weakly_leaderboard.iloc[i].items():
            if Gold_Medal in str(value):
                g_count +=1
            if Silver_Medal in str(value):
                s_count +=1
            if Bronze_Medal in str(value):
                b_count +=1
        Total_Medals_Count.append(g_count * 1.03 + s_count * 1.02 + b_count * 1.01)
        Total_Medals.append(g_count * Gold_Medal + s_count * Silver_Medal + b_count * Bronze_Medal)
    weakly_leaderboard['Total'] = pd.Series(Total_Medals)
    weakly_leaderboard['MedalCount'] = pd.Series(Total_Medals_Count)
    weakly_leaderboard = weakly_leaderboard.sort_values('MedalCount',ascending=False,ignore_index=True)
    weakly_leaderboard = weakly_leaderboard.drop('MedalCount', axis=1)
    weakly_leaderboard = weakly_leaderboard.drop(columns=['FGM','FGA','FG','FTM','FTA','FT','threePtm','Points','Rebound','Assists','Steal','Block','To','Is_Major'])
    st.dataframe(weakly_leaderboard, height=600, use_container_width=True)

def power_ranking():
    global week_matchups
    power_ranking_df = pd.DataFrame(columns=['Team_Name', 'totaleWLT', 'avgeWLT', 'Score'], index=range(16))

    hard_dict = {}
    for week in weeks_list:
        matchups = lg.matchups(week=week.split(' ')[1])
        week_matchups = matchups['fantasy_content']['league'][1]['scoreboard']['0']['matchups']
        weekly_team_stats = get_team_stats("", major_bool=False)

        for team in teams_list:
            chg_idx = week_team_stats[weekly_team_stats['Team_Name'] == team].index
            weekly_team_stats.loc[chg_idx, 'Is_Major'] = True
            map = get_cross_map()
            weekly_team_stats.loc[chg_idx, 'Is_Major'] = False
            ewlt_map = ewlt_get(cross_points_df)
            if team not in hard_dict:
                hard_dict[team] = {}
            hard_dict[team][week] = {
                'Win': ewlt_map['Win'],
                'Lose': ewlt_map['Lose'],
                'Tie': ewlt_map['Tie'],
            }
    aggregate_scores = {}

    for team, weeks in hard_dict.items():
        win_total = 0
        lose_total = 0
        tie_total = 0
        num_weeks = len(weeks)

        for week, scores in weeks.items():
            if not scores['Tie'] == 9:
                win_total += scores['Win']
                lose_total += scores['Lose']
                tie_total += scores['Tie']

        aggregate_scores[team] = {
            'TWin': win_total,
            'TLose': lose_total,
            'TTie': tie_total,
            'AWin': win_total / num_weeks if num_weeks else 0,
            'ALose': lose_total / num_weeks if num_weeks else 0,
            'ATie': tie_total / num_weeks if num_weeks else 0,
            'Total': win_total + (tie_total/2)
        }
         
    idx = 0
    for team, scores in aggregate_scores.items():
        power_ranking_df.loc[idx].Team_Name = team
        power_ranking_df.loc[idx].totaleWLT = format(scores['TWin'], '.2f') + "-" + format(scores['TLose'],
                                                                                        '.2f') + "-" + format(
            scores['TTie'], '.2f')
        power_ranking_df.loc[idx].avgeWLT = format(scores['AWin'], '.2f') + "-" + format(scores['ALose'],
                                                                                      '.2f') + "-" + format(
            scores['ATie'], '.2f')
        power_ranking_df.loc[idx].Score = scores['Total']
        idx += 1

    return power_ranking_df

def team_info(i,team_name):
    set_rosters(team_name)
    workers = compare_rosters()
    per_draft = percentage(rosters['draft'],'draft')
    per_loyals = percentage(rosters['loyals'],'loyals')
    per_todays = percentage(rosters['today'],'today') 
    team_info_df.loc[i].Team_Name = team_name
    team_info_df.loc[i].All_Squad = len(rosters['today'])
    if sub_mode_select == "Loyalty":     
        team_info_df.loc[i].Loyalty_Score = len(rosters['loyals']) * 0.6 + workers * 0.25 - int(teams[teams_list[team_name]]['number_of_trades']) * 0.1 - teams[teams_list[team_name]]['number_of_moves'] * 0.05
        team_info_df.loc[i].Power_of_Loyals = per_loyals['avr_por']
        team_info_df.loc[i].Num_of_Loyals = len(rosters['loyals'])
        team_info_df.loc[i].Num_of_Workers = workers
        team_info_df.loc[i].Num_of_Trades = int(teams[teams_list[team_name]]['number_of_trades'])
        team_info_df.loc[i].Num_of_Moves = teams[teams_list[team_name]]['number_of_moves']
    elif sub_mode_select == "Healthy":
        inj_list = injury_list_today()
        a=2 if inj_list['status'][2]+inj_list['status'][3] > 2 else inj_list['status'][2]+inj_list['status'][3]
        b=inj_list['status'][2]+inj_list['status'][3]-2 if inj_list['status'][2]+inj_list['status'][3] > 2 else 0
        team_info_df.loc[i].Daily_Healthy_Score = 1 - (a*0.75 + b*1 + 0.25* inj_list['status'][1]) / 13
        team_info_df.loc[i].Healthy = inj_list['status'][0]
        team_info_df.loc[i].GTD = inj_list['status'][1]
        team_info_df.loc[i].Out = inj_list['status'][2]
        team_info_df.loc[i].Inj = inj_list['status'][3]
        team_info_df.loc[i].H_APOR = float(format(inj_list['avrg_status'][0], '.1f'))
        team_info_df.loc[i].G_APOR = float(format(inj_list['avrg_status'][1], '.1f'))
        team_info_df.loc[i].O_APOR = float(format(inj_list['avrg_status'][2], '.1f'))
        team_info_df.loc[i].I_APOR = float(format(inj_list['avrg_status'][3], '.1f'))
        team_info_df.loc[i].Hospital_Days = injury_list(team_name)
    elif sub_mode_select == "Story Mode":
        team_info_df.loc[i].Masters_of_the_Ship = per_loyals['e100']
        team_info_df.loc[i].Right_Hands = per_loyals['o95'] - per_loyals['e100']
        team_info_df.loc[i].Pioneers = per_loyals['o90'] - per_loyals['o95']   
        team_info_df.loc[i].Knights = per_loyals['o80'] - per_loyals['o90']   
        team_info_df.loc[i].Domestiques = per_loyals['o50'] - per_loyals['o80']   
        team_info_df.loc[i].Sons = len(rosters['loyals']) - per_loyals['o50']   
        team_info_df.loc[i].Hippocrates = per_todays['o98'] - per_loyals['o98']
        team_info_df.loc[i].Legionnaire = per_todays['o80'] - per_loyals['o80'] - team_info_df.loc[i].Hippocrates
        team_info_df.loc[i].Soldier_of_Fortune = per_todays['o40'] - per_loyals['o40'] - team_info_df.loc[i].Legionnaire - team_info_df.loc[i].Hippocrates
        team_info_df.loc[i].Tails = len(rosters['today']) - len(rosters['loyals']) - team_info_df.loc[i].Hippocrates - team_info_df.loc[i].Legionnaire - team_info_df.loc[i].Soldier_of_Fortune       
    elif sub_mode_select == "Profile":
        team_info_df.loc[i].Profile = ""
        team_info_df.loc[i].Avrg_Per_of_Rostered = format(per_todays['avr_por'], '.2f')
        team_info_df.loc[i].Avrg_Per_of_Loyals = format(per_loyals['avr_por'], '.2f')
        team_info_df.loc[i].Avrg_Per_of_Drafted = format(per_draft['avr_por'], '.2f')
        team_info_df.loc[i].Num_of_Loyals = str(len(rosters['loyals']))+"/13"
        team_info_df.loc[i].Hospital_Days = injury_list(team_name)
        
    #team_info_df.loc[i].Cur_Week_Adds = int(teams[teams_list[team_name]]['roster_adds']['value'])
    #team_info_df.loc[i].Over40_POR = per_todays['o40']
    #team_info_df.loc[i].Over50_POR = per_todays['o50']
    #team_info_df.loc[i].Over60_POR = per_todays['o60']
    #team_info_df.loc[i].Over80_POR = per_todays['o80']
    #team_info_df.loc[i].Over90_POR = per_todays['o90']
    #team_info_df.loc[i].Over95_POR = per_todays['o95']
    #team_info_df.loc[i].Equal100_POR = per_todays['e100']
    #team_info_df.loc[i].Under40_POR = len(rosters['today']) - per_todays['o40']
    #team_info_df.loc[i].Under20_POR = per_todays['u20']
    #team_info_df.loc[i].Under10_POR = per_todays['u10']

    return team_info_df

#team_key = teams_list[team_select]
#team = lg.to_team(team_key)
#with open('rosters.txt', 'a') as f:
#    f.write(team_select + '\n')
#for i in range(int(start_day.strftime("%Y")),int(today.strftime("%Y"))+1):
#    for j in range(int(start_day.strftime("%m")),int(today.strftime("%m"))+1):
#        for k in range(1,32):
#            if ( j == 10 and k < int(start_day.strftime("%d")) ):
#                continue
#            elif ( j == int(today.strftime("%m")) and k > int(today.strftime("%d")) ):
#                break 
#            try:
#                day =  datetime.date(i, j, k)
#            except:
#                continue
#            team_roster = team.roster(day=day)
#            with open('rosters.txt', 'a') as f:
#                f.write(str(day) + '\n')
#                f.write(str(team_roster) + '\n')

def injury_list(team_name):
    il_sum = 0
    statLineStart = False
    with open('rosters.txt', 'r') as f:
        for x in f:
            x = x.strip()
            aTeam = False
            theTeam = False

            if x[0:2] == "20":
                continue
            for team in teams_list:
                if x == team:  
                    aTeam = True
                    if x == team_name:
                        theTeam = True
                        statLineStart = True 
                    break
            if aTeam == True:
                if statLineStart == True and theTeam == False:
                    statLineStart = False   
                continue

            if statLineStart:
                x = x.replace("{\'", "{\"")
                x = x.replace("\'}", "\"}")
                x = x.replace("[\'", "[\"")
                x = x.replace("\']", "\"]")
                x = x.replace("\' ", "\" ")
                x = x.replace(" \'", " \"")
                x = x.replace(":\'", ":\"")
                x = x.replace("\':", "\":")
                x = x.replace(",\'", ",\"")
                x = x.replace("\',", "\",")
                team_day_roster = json.loads(x)
                if len(team_day_roster) > 0:
                    if team_day_roster[-1]['selected_position'] == 'IL' or team_day_roster[-1]['selected_position'] == 'IL+':
                        il_sum += 1
                        if team_day_roster[-2]['selected_position'] == 'IL':
                            il_sum += 1
    return il_sum

def injury_list_today():
    status = {'status' : [0, 0, 0, 0], 'avrg_status' : [0 ,0 ,0 ,0]}
    for player in team_roster:
        if player['status'] == 'INJ':
            status['status'][3] += 1
            for player_owned in percent_owned: status['avrg_status'][3] += player_owned['percent_owned'] if player['player_id'] == player_owned['player_id'] else 0 
        elif player['status'] == 'O':
            status['status'][2] += 1
            for player_owned in percent_owned: status['avrg_status'][2] += player_owned['percent_owned'] if player['player_id'] == player_owned['player_id'] else 0
        elif player['status'] == 'GTD':
            status['status'][1] += 1
            for player_owned in percent_owned: status['avrg_status'][1] += player_owned['percent_owned'] if player['player_id'] == player_owned['player_id'] else 0
        else:
            status['status'][0] += 1
            for player_owned in percent_owned: status['avrg_status'][0] += player_owned['percent_owned'] if player['player_id'] == player_owned['player_id'] else 0

    for i in range(0,4): status['avrg_status'][i] = (status['avrg_status'][i] / status['status'][i]) if status['status'][i] != 0 else 0
    return status

def percentage(roster, roster_name):
    global percent_owned
    per_dict = {'draft':{'sum_por':0,'avr_por':0,'e100':0,'o98':0,'o95':0,'o90':0,'o80':0,'o60':0,'o50':0,'o40':0,'u20':0,'u10':0}, 
                'loyals':{'sum_por':0,'avr_por':0,'e100':0,'o98':0,'o95':0,'o90':0,'o80':0,'o60':0,'o50':0,'o40':0,'u20':0,'u10':0}, 
                'today':{'sum_por':0,'avr_por':0,'e100':0,'o98':0,'o95':0,'o90':0,'o80':0,'o60':0,'o50':0,'o40':0,'u20':0,'u10':0}}
    percent_owned = lg.percent_owned(roster)
    for player_owned in percent_owned:
        per_dict[roster_name]['sum_por'] += player_owned['percent_owned']
        per_dict[roster_name]['e100'] += 1 if player_owned['percent_owned'] == 100 else 0
        per_dict[roster_name]['o98'] += 1 if player_owned['percent_owned'] >= 98 else 0
        per_dict[roster_name]['o95'] += 1 if player_owned['percent_owned'] >= 95 else 0
        per_dict[roster_name]['o90'] += 1 if player_owned['percent_owned'] >= 90 else 0
        per_dict[roster_name]['o80'] += 1 if player_owned['percent_owned'] >= 80 else 0
        per_dict[roster_name]['o60'] += 1 if player_owned['percent_owned'] >= 60 else 0
        per_dict[roster_name]['o50'] += 1 if player_owned['percent_owned'] >= 50 else 0
        per_dict[roster_name]['o40'] += 1 if player_owned['percent_owned'] >= 40 else 0
        per_dict[roster_name]['u20'] += 1 if player_owned['percent_owned'] < 20 else 0
        per_dict[roster_name]['u10'] += 1 if player_owned['percent_owned'] < 10 else 0
    per_dict[roster_name]['avr_por'] = (per_dict[roster_name]['sum_por'] / len(percent_owned))
    return per_dict[roster_name]

def set_rosters(team_name):
    global team_roster
    global rosters
    rosters = {}
    roster_ids = []
    team_key = teams_list[team_name]
    team = lg.to_team(team_key)     #team = yfa.team.Team(sc, team_key)
    # draft roster
    #tra = lg.transactions('trade','')
    #print(tra)
    for i in range(0,208):
        if draft_res[i]['team_key'] == team_key:
            roster_ids.append(draft_res[i]['player_id'])  #pId = draft_res[i]['player_id']: roster_draft.append(lg.player_details([pId])[0]['name']['full'])
    rosters['draft'] = roster_ids
    # week rosters
    for week in weeks_list:
        roster_ids = []
        team_roster = team.roster(week=week.split(' ')[1])
        for i in range(0,len(team_roster)):
            roster_ids.append(team_roster[i]['player_id'])
        rosters[week] = roster_ids
    # today's roster  
    roster_ids = []
    team_roster = team.roster()
    num_of_players = len(team_roster)
    for i in range(0,num_of_players):
        roster_ids.append(team_roster[i]['player_id'])
    rosters['today'] = roster_ids

def compare_rosters():   
    #loyals --> players that teams drafted and still have 
    #workers --> players that teams didn't draft but had 4/5 of the weeks
    roster_ids = []
    sum_of_workers = 0
    for player_today in rosters['today']:
        for player_draft in rosters['draft']:
            if player_today == player_draft:
                roster_ids.append(player_draft)
        sum_of_week=0
        for week in weeks_list:
            for player_week in rosters[week]:
                if player_today == player_week:
                    sum_of_week += 1 
        sum_of_workers +=1 if sum_of_week > len(weeks_list)*(0.8) else 0
    rosters['loyals'] = roster_ids
    sum_of_workers -= len(rosters['loyals'])
    return sum_of_workers

def sort(array, arrayIdx):
    n = len(array)
    for i in range(n):
        already_sorted = True
        for j in range(n - i - 1):
            if array[j] < array[j + 1]:
                array[j], array[j + 1] = array[j + 1], array[j]
                arrayIdx[j], arrayIdx[j + 1] = arrayIdx[j + 1], arrayIdx[j]
                already_sorted = False
        if already_sorted:
            break
    return array, arrayIdx

if mode_select == "Alternate Universe":
    st.write("#### Alternate " + week_select+ "'s")
    st.write("###### for " + team_select.upper())
    st.write("")
    st.write("")

    matchups = lg.matchups(week=week_select.split(' ')[1])
    week_matchups = matchups['fantasy_content']['league'][1]['scoreboard']['0']['matchups']
    weekly_team_stats = get_team_stats(team_select, major_bool = True)
    get_cross_map()
    update_other_team_color()
    df_color_codes = cross_color_df.map(color_map.get)
    style_cross = cross_points_df.style.apply(apply_color, colors=df_color_codes, axis=None)
    st.dataframe(style_cross, height=600, use_container_width=True)
    ##Expected WLT eWLT Calculate
    ewlt_map = ewlt_get(cross_points_df)
    st.write( team_select + " " +  week_select + " expected win-lose-tie value (eWLT) is : " + format(ewlt_map["Win"], '.2f') + "-" + format(ewlt_map["Lose"], '.2f') + "-" + format(ewlt_map["Tie"], '.2f'))

elif mode_select == "Power Rankings":
    color_skirt_df = pd.DataFrame(columns=['Team_Name', 'totaleWLT', 'avgeWLT', 'Score'], index=range(16))
    color_skirt_df.fillna("None", inplace=True)
    power_ranking_df = power_ranking()
    
    power_ranking_df = power_ranking_df.sort_values(by=['Score'], ascending=False)
    power_ranking_df = power_ranking_df.reset_index(drop=True)
    power_ranking_df['Score'] = power_ranking_df['Score'].map('{:.2f}'.format)
    chg = power_ranking_df[power_ranking_df['Team_Name'] == team_select].index
    color_skirt_df.loc[chg] = "Match"
    df_color_codes = color_skirt_df.map(color_map_total.get)
    style_cross = power_ranking_df.style.apply(apply_color, colors=df_color_codes, axis=None)
    st.dataframe(style_cross, height=600, use_container_width=True)

elif mode_select == "Medal Board":
    render_medal_board()

elif mode_select == "Alternate Universe - Matchups":
    st.write("#### Alternate Matchups")
    st.write("###### between " + team_select.upper() + " and " + matchup_select.upper())
    st.write("")
    st.write("")

    get_cross_map_matchup()

elif mode_select == "Box Plots":
    if sub_mode_select == "Box - Weekly" or sub_mode_select == "Box & SD - Weekly":
        matchups = lg.matchups(week=week_select.split(' ')[1])
        week_matchups = matchups['fantasy_content']['league'][1]['scoreboard']['0']['matchups']
        team_stats = get_team_stats(team_select, major_bool = True)
        title = " - Week "+week_select.split(' ')[1]
        if sub_mode_select == "Box - Weekly":
            boxMean = True
        else:
            boxMean = "sd"
    elif sub_mode_select == "Box - Total":
        team_stats = get_total_team_stats(team_select, major_bool = True)
        title = " - Total"
        boxMean = True
    #team_stats = team_stats.drop(columns=['FGM','FGA','FTA','FTM'])

    major_df = team_stats.loc[team_stats['Is_Major'] == True]
    major_df = major_df.reset_index(drop=True)

    categoies = {0: 'Team_Name', 1:'FG', 2:'FT', 3:'threePtm', 4:'Points', 5:'Rebound', 6:'Assists', 7:'Steal', 8:'Block', 9:'To'}

    for i in range(1, 10):
        fig = go.Figure()
        fig.add_trace(go.Box(y=team_stats[categoies[i]], name= categoies[i]+title, boxmean=boxMean))
        highlight_trace = go.Scatter(x=[major_df.loc[0].Team_Name],y=[major_df[categoies[i]][0]],mode='markers', marker=dict(size=10, color='red'),name=major_df[categoies[0]][0])
        fig.add_trace(highlight_trace)
        st.plotly_chart(fig, use_container_width=False, theme="streamlit")

elif mode_select == "Total Stats":
    color_total_df = pd.DataFrame(columns=['Team_Name', 'FGM', 'FGA', 'FG', 'FTM', 'FTA', 'FT', 'threePtm', 'Points', 'Rebound', 'Assists', 'Steal', 'Block', 'To'],index=range(16))    
    color_total_df.fillna("None", inplace=True)
    
    team_stats = get_total_team_stats(team_select, major_bool = True)
    team_stats = team_stats.drop(columns=['Is_Major'])
    
    chg = team_stats[team_stats['Team_Name'] == team_select].index
    color_total_df.loc[chg] = "Match"
    df_color_codes = color_total_df.map(color_map_total.get)
    style_cross = team_stats.style.apply(apply_color, colors=df_color_codes, axis=None)
    st.dataframe(style_cross, height=600, use_container_width=True)

elif mode_select == "Team Info":
    if sub_mode_select == "Profile":
        st.write("#### Team Profiles")
        team_info_df = pd.DataFrame(columns=['Team_Name','Profile','Avrg_Per_of_Rostered','Avrg_Per_of_Loyals','Avrg_Per_of_Drafted','Num_of_Loyals','All_Squad','Hospital_Days'],index=range(16))
        color_info_df = pd.DataFrame(columns=['Team_Name','Profile','Avrg_Per_of_Rostered','Avrg_Per_of_Loyals','Avrg_Per_of_Drafted','Num_of_Loyals','All_Squad','Hospital_Days'],index=range(16))
        color_info_df.fillna("None", inplace=True)
    elif sub_mode_select == "Loyalty":
        st.write("#### Teams' Loyalty to Players")
        team_info_df = pd.DataFrame(columns=['Team_Name','Loyalty_Score','Power_of_Loyals','All_Squad','Num_of_Loyals','Num_of_Workers','Num_of_Trades','Num_of_Moves'],index=range(16))
        color_info_df = pd.DataFrame(columns=['Team_Name','Loyalty_Score','Power_of_Loyals','All_Squad','Num_of_Loyals','Num_of_Workers','Num_of_Trades','Num_of_Moves'],index=range(16))        
        color_info_df.fillna("None", inplace=True)
    elif sub_mode_select == "Healthy":
        st.write("#### Health Conditions of Teams")
        team_info_df = pd.DataFrame(columns=['Team_Name','All_Squad','Daily_Healthy_Score','Hospital_Days','Healthy','H_APOR','GTD','G_APOR','Out','O_APOR','Inj','I_APOR'],index=range(16))
        color_info_df = pd.DataFrame(columns=['Team_Name','All_Squad','Daily_Healthy_Score','Hospital_Days','Healthy','H_APOR','GTD','G_APOR','Out','O_APOR','Inj','I_APOR'],index=range(16))
        color_info_df.fillna("None", inplace=True)
    elif sub_mode_select == "Story Mode":
        st.write("#### Story Mode")
        st.write("Players have roles and these show power of team and profile of manager")
        st.write("Master of the ship leads the league and Hippocrates heal the team by coming with a trade. Manager who has Sons is too loyal and manager who has Hippocrates, Legionnaire etc is a trader. ")

        team_info_df = pd.DataFrame(columns=['Team_Name','All_Squad','Masters_of_the_Ship','Right_Hands','Pioneers','Knights','Domestiques','Sons','Hippocrates','Legionnaire','Soldier_of_Fortune','Tails'],index=range(16))
        color_info_df = pd.DataFrame(columns=['Team_Name','All_Squad','Masters_of_the_Ship','Right_Hands','Pioneers','Knights','Domestiques','Sons','Hippocrates','Legionnaire','Soldier_of_Fortune','Tails'],index=range(16))
        color_info_df.fillna("None", inplace=True)

    i=0
    for team_name in teams_list:
        team_info_df = team_info(i,team_name)
        i+=1

    if sub_mode_select == "Profile":
        power_ranking_df = power_ranking()
       
        array=[]
        arrayIdx=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
        for i in range(16):
            array.append(((float(team_info_df.loc[i].Avrg_Per_of_Rostered)+float(team_info_df.loc[i].Avrg_Per_of_Loyals)+float(team_info_df.loc[i].Avrg_Per_of_Drafted))/3)+(power_ranking_df.loc[i].Score/81*100))
        sort(array, arrayIdx)
        for i in range(2):
            team_info_df.loc[arrayIdx[i]].Profile = team_info_df.loc[arrayIdx[i]].Profile + "/ Top /"
        for i in [2,3,4,5]:
            team_info_df.loc[arrayIdx[i]].Profile = team_info_df.loc[arrayIdx[i]].Profile + "/ Contender /"

        max = 0 
        for i in range(16):
            max = float(team_info_df.loc[i].Avrg_Per_of_Drafted) if float(team_info_df.loc[i].Avrg_Per_of_Drafted) > max else max 
        for i in range(16):
            if float(team_info_df.loc[i].Avrg_Per_of_Drafted) == max:
                team_info_df.loc[i].Profile = team_info_df.loc[i].Profile + "/ Draft Crafter /"

        array=[]
        arrayIdx=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
        for i in range(16):
            array.append(int(team_info_df.loc[i].Num_of_Loyals.split('/')[0]))       
        sort(array, arrayIdx)
        for i in [15,14,13]:
            team_info_df.loc[arrayIdx[i]].Profile = team_info_df.loc[arrayIdx[i]].Profile + "/ Merchant /"

        for i in range(16):
            if team_info_df.loc[i].Hospital_Days >= 85:
                team_info_df.loc[i].Profile = team_info_df.loc[i].Profile + "/ Injury Prone /"

    idx = team_info_df[team_info_df['Team_Name'] == team_select].index
    color_info_df.loc[idx, 'Team_Name'] = "Match"
    color_info_df.loc[idx, 'Profile'] = "Match"
    df_color_codes = color_info_df.map(color_map_total.get)
    style_cross = team_info_df.style.apply(apply_color, colors=df_color_codes, axis=None) 

    strInfo = """
    ```
    >                                  Top:   2 teams at the top / Tepedeki 2 takım
    >                            Contender:   Other contender teams for the top / Tepeye aday diğer takımlar
    >                               Loyals:   Players that team drafted and still have / Takımın draft ettiği ve hala takımda bulunan oyuncuların sayısı
    >   Average Percent of Rostered (APOR):   Average percentage ownership of the team's players across all Yahoo leagues / Takımdaki oyuncuların tüm Yahoo liglerinin yüzde kaçında sahipli olduğunun ortalaması
    >            Average Percent of Loyals:   Average percentage ownership of players in the 'Loyals' category across all Yahoo leagues / 'Loyals' kategorisindeki oyuncuların tüm Yahoo liglerinin yüzde kaçında sahipli olduğunun ortalaması
    >           Average Percent of Drafted:   Average percentage ownership of drafted players across all Yahoo leagues / Draft edilen oyuncuların tüm Yahoo liglerinin yüzde kaçında sahipli olduğunun ortalaması
    >                        Hospital Days:   Total number of days in which IL and IL+ positions were occupied (Based on data from the first 50 days.) / IL ve IL+ pozisyonlarının dolu geçirildiği toplam gün sayısı (İlk 50 günlük veri baz alınmıştır.)
    >                              Workers:   Players that team didn't draft but had 4/5 of the weeks / Takımın draft etmediği ancak haftaların 4/5'inde takımda olan oyuncular 
    ```
    """
    st.write(strInfo)
    st.dataframe(style_cross, height=600, use_container_width=True)