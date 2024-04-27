import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///fantasy.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/favorites", methods=["GET", "POST"])
@login_required
def favorites():
    """Display a table of the favorited Nfl players"""
    if request.method == "POST":
        # Return error message if submit with nothing selected
        if not request.form.get("position_select") and not request.form.get("team_select"):
            return apology("must provide position or team", 400)
        # if only filter by position
        elif not request.form.get("team_select") and request.form.get("position_select"):
            team = "All Teams"
            position = request.form.get("position_select")
            favorites = db.execute("SELECT * FROM players_2021 WHERE id IN (SELECT player_id FROM favorites WHERE user_id = ?) AND abbreviated_position = ? ORDER BY name", session["user_id"], position)
        # if only filter by team
        elif not request.form.get("position_select") and request.form.get("team_select"):
            team = request.form.get("team_select")
            position = "Player"
            favorites = db.execute("SELECT * FROM players_2021 WHERE id IN (SELECT player_id FROM favorites WHERE user_id = ?) AND abbreviated_team = ? ORDER BY name", session["user_id"], team)
        # if filter by team and position
        else:
            position = request.form.get("position_select")
            team = request.form.get("team_select")
            favorites = db.execute("SELECT * FROM players_2021 WHERE id IN (SELECT player_id FROM favorites WHERE user_id = ?) AND abbreviated_position = ? AND abbreviated_team = ? ORDER BY name", session["user_id"], position, team)

        # Configure a list of the nfl teams and positions to be used in display
        positions = db.execute("SELECT * FROM positions")
        teams = db.execute("SELECT team, abbreviation FROM nfl_teams ORDER BY team")

        # Send user to the filtered favorites page
        return render_template("favorites.html", favorites=favorites, positions=positions, teams=teams, team=team, position=position)

    else:
        """Display a table of the favorited Nfl players"""
        # return all favorites for given user
        favorites = db.execute("SELECT * FROM players_2021 WHERE id IN (SELECT player_id FROM favorites WHERE user_id = ?) ORDER BY name", session["user_id"])

        # Configure a list of the nfl teams and positions to be used in display
        positions = db.execute("SELECT * FROM positions")
        teams = db.execute("SELECT team, abbreviation FROM nfl_teams ORDER BY team")

        # show default values for player page
        team = "All Teams"
        position = "Player"

        # Send user to the favorites page
        return render_template("favorites.html", favorites=favorites, positions=positions, teams=teams, team=team, position=position)


@app.route("/")
@login_required
def index():
    """Display the home page of the Fantasy Site"""

    return render_template("index.html")


@app.route("/players", methods=["GET", "POST"])
@login_required
def players():
    """Display a table of the Nfl players"""
    if request.method == "POST":
        # Return error message if submit with nothing selected
        if not request.form.get("position_select") and not request.form.get("team_select"):
            return apology("must provide position or team", 400)
        # if only filter by position
        elif not request.form.get("team_select") and request.form.get("position_select"):
            team = "All Teams"
            position = request.form.get("position_select")
            players = db.execute("SELECT * FROM players_2021 WHERE abbreviated_position = ? ORDER BY name ", position)
        # if only filter by team
        elif not request.form.get("position_select") and request.form.get("team_select"):
            team = request.form.get("team_select")
            position = "Player"
            players = db.execute("SELECT * FROM players_2021 WHERE abbreviated_team = ? ORDER BY name ", team)
        # if filter by team and position
        else:
            position = request.form.get("position_select")
            team = request.form.get("team_select")
            players = db.execute("SELECT * FROM players_2021 WHERE abbreviated_team = ? AND abbreviated_position = ? ORDER BY name ", team, position)

        # Configure a list of the nfl teams and positions to be used in display
        positions = db.execute("SELECT * FROM positions")
        teams = db.execute("SELECT team, abbreviation FROM nfl_teams ORDER BY team")

        # display the filtered players page
        return render_template("players.html", players=players, positions=positions, teams=teams, favorites=favorites, team=team, position=position)
    else:
        """Display a table of the Nfl players"""
        # get the players from 2021
        players = db.execute("SELECT * FROM players_2021 WHERE abbreviated_position = ? ORDER BY name", 'QB')

        # Configure a list of the nfl teams and positions to be used in display
        positions = db.execute("SELECT * FROM positions")
        teams = db.execute("SELECT team, abbreviation FROM nfl_teams ORDER BY team")

        # show default values for player page
        team = "All Teams"
        position = "QB"

        # dsiaply players page
        return render_template("players.html", players=players, positions=positions, teams=teams, favorites=favorites, team=team, position=position)


@app.route("/player_page", methods=["GET", "POST"])
@login_required
def player_page():
    """Display player page of given player ID and Fav/Unfav the player"""
    if request.method == "POST":
        if not request.form.get("player_id"):
            return apology("must provide player", 400)
        player_id = int(request.form.get("player_id"))

         # record which players the user has favorited
        favorites = []
        favs = db.execute("SELECT player_id FROM favorites WHERE user_id = ?", session["user_id"])
        for dict in favs:
            favorites.append(int(dict['player_id']))

        # Either remove or add player into favorites
        if player_id in favorites:
            db.execute("DELETE FROM favorites WHERE user_id = ? AND player_id = ?", session["user_id"], player_id)
            favorites.remove(int(dict['player_id']))
        else:
            db.execute("INSERT INTO favorites (user_id, player_id) VALUES (?, ?)", session["user_id"], player_id)
            favorites.append(int(player_id))

        # Get the player info for the selected player
        player = db.execute("SELECT * FROM players_2021 WHERE id = ?", player_id)[0]

        # Get all stats for specific player
        stat_categories = [
                'fumbles', 'completions', 'interceptionsThrown', 'netPassingYards', 'passingAttempts',
                'passingTouchdowns', 'twoPtPass', 'rushingTouchdowns', 'rushingYards', 'twoPtRush',
                'receivingTargets', 'receivingTouchdowns', 'receivingYards', 'receptions', 'twoPtReception',
                'defensiveTouchdowns', 'kicksBlocked', 'passesBattedDown', 'twoPtReturns', 'sacks',
                'safeties', 'yardsAllowed', 'pointsAllowed', 'interceptions', 'fumblesRecovered', 'extraPointAttempts', 'extraPointsMade',
                'fieldGoalsMade1_19', 'fieldGoalsMade20_29', 'fieldGoalsMade30_39', 'fieldGoalsMade40_49', 'fieldGoalsMade50',
                'touchbacks', 'kickReturnTouchdowns', 'kickReturnYards', 'puntReturnTouchdowns', 'puntReturnYards'
        ]

        # Converts stat names to display names and vice versa
        display_names = {}
        compact_names = {}
        name_dict = db.execute(f"SELECT displayName, name FROM stats")
        for dict in name_dict:
            display_names[dict['name']] = dict['displayName']
            compact_names[dict['displayName']] = dict['name']

        # Get the total season stats and filter by only stats that are non-zero for whole season
        season_stats = {}
        for i in range(len(stat_categories)):
            stat_dict = db.execute(f"SELECT SUM({stat_categories[i]}) AS {stat_categories[i]} FROM stats_2021 WHERE athlete_id = ? or defense_id = ?", player_id, player_id)[0]
            if stat_dict[stat_categories[i]] != 0:
                season_stats[display_names[stat_categories[i]]] = stat_dict[stat_categories[i]]

        # Get the total stats - only need to get those for where toal not equal to 0
        total_stats = []
        for j in range(1, 19):
            weekly_stats = {}
            if not db.execute(f"SELECT week FROM stats_2021 WHERE week = ? AND athlete_id = ? OR week = ? AND defense_id = ?", j, player_id, j, player_id):
                pass
            else:
                weekly_stats['week'] = j
                for stat in season_stats:
                    key = compact_names[stat]
                    stat_dict = db.execute(f"SELECT {key} FROM stats_2021 WHERE week = ? AND athlete_id = ? OR week = ? AND defense_id = ?", j, player_id, j, player_id)[0]
                    weekly_stats[display_names[key]] = stat_dict[key]
                total_stats.append(weekly_stats)

        # Get fantasy scores for player using user values
        #get list of stat values for current person
        stats_value = db.execute("SELECT * FROM user_stat_values WHERE user_id = ?", session["user_id"])[0]
        del stats_value["user_id"]

        #get the score for each week
        weekly_scores = {}
        for dict in total_stats:
            score = 0
            for key in dict:
                if key != "week":
                    score += round(dict[key] * stats_value[compact_names[key]], 2)
            weekly_scores[dict["week"]] = round(score, 2)

        # get the score for the season
        season_score = 0
        for week in weekly_scores:
            season_score += weekly_scores[week]
        season_score = round(season_score, 2)

        # display player info page
        return render_template("player_page.html", player=player, total_stats=total_stats, season_stats=season_stats, favorites=favorites, weekly_scores=weekly_scores, season_score=season_score)
    else:
        """Display player page of given player ID"""

        player_id = request.args.get("player_id")
        player = db.execute("SELECT * FROM players_2021 WHERE id = ?", player_id)[0]

        # Get all stats for specific player
        stat_categories = [
                'fumbles', 'completions', 'interceptionsThrown', 'netPassingYards', 'passingAttempts',
                'passingTouchdowns', 'twoPtPass', 'rushingTouchdowns', 'rushingYards', 'twoPtRush',
                'receivingTargets', 'receivingTouchdowns', 'receivingYards', 'receptions', 'twoPtReception',
                'defensiveTouchdowns', 'kicksBlocked', 'passesBattedDown', 'twoPtReturns', 'sacks',
                'safeties', 'yardsAllowed', 'pointsAllowed', 'interceptions', 'fumblesRecovered', 'extraPointAttempts', 'extraPointsMade',
                'fieldGoalsMade1_19', 'fieldGoalsMade20_29', 'fieldGoalsMade30_39', 'fieldGoalsMade40_49', 'fieldGoalsMade50',
                'touchbacks', 'kickReturnTouchdowns', 'kickReturnYards', 'puntReturnTouchdowns', 'puntReturnYards'
        ]

        # Converts stat names to display names and vice versa
        display_names = {}
        compact_names = {}
        name_dict = db.execute(f"SELECT displayName, name FROM stats")
        for dict in name_dict:
            display_names[dict['name']] = dict['displayName']
            compact_names[dict['displayName']] = dict['name']

        # Get the total season stats and filter by only stats that are non-zero for whole season
        season_stats = {}
        for i in range(len(stat_categories)):
            stat_dict = db.execute(f"SELECT SUM({stat_categories[i]}) AS {stat_categories[i]} FROM stats_2021 WHERE athlete_id = ? or defense_id = ?", player_id, player_id)[0]
            if stat_dict[stat_categories[i]] != 0:
                season_stats[display_names[stat_categories[i]]] = stat_dict[stat_categories[i]]

        # Get the total stats - only need to get those for where toal not equal to 0
        total_stats = []
        for j in range(1, 19):
            weekly_stats = {}
            if not db.execute(f"SELECT week FROM stats_2021 WHERE week = ? AND athlete_id = ? OR week = ? AND defense_id = ?", j, player_id, j, player_id):
                pass
            else:
                weekly_stats['week'] = j
                for stat in season_stats:
                    key = compact_names[stat]
                    stat_dict = db.execute(f"SELECT {key} FROM stats_2021 WHERE week = ? AND athlete_id = ? OR week = ? AND defense_id = ?", j, player_id, j, player_id)[0]
                    weekly_stats[display_names[key]] = stat_dict[key]
                total_stats.append(weekly_stats)

        # record which players the user has favorited
        favorites = []
        favs = db.execute("SELECT player_id FROM favorites WHERE user_id = ?", session["user_id"])
        for dict in favs:
            favorites.append(dict['player_id'])

        # Get fantasy scores for player using user values
        #get list of stat values for current person
        stats_value = db.execute("SELECT * FROM user_stat_values WHERE user_id = ?", session["user_id"])[0]
        del stats_value["user_id"]

        #get the score for each week
        weekly_scores = {}
        for dict in total_stats:
            score = 0
            for key in dict:
                if key != "week":
                    score += round(dict[key] * stats_value[compact_names[key]], 2)
            weekly_scores[dict["week"]] = round(score, 2)

        # get the score for the season
        season_score = 0
        for week in weekly_scores:
            season_score += weekly_scores[week]
        season_score = round(season_score, 2)

        # display player info page
        return render_template("player_page.html", player=player, total_stats=total_stats, season_stats=season_stats, favorites=favorites, weekly_scores=weekly_scores, season_score=season_score)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # If user has no fantasy value system, generate default one
        if not db.execute("SELECT user_id FROM user_stat_values WHERE user_id = ?", session["user_id"]):
            db.execute("INSERT INTO user_stat_values (user_id) VALUES (?)", session["user_id"])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        if not request.form.get("confirmation"):
            return apology("must provide password confirmation", 400)

        # Check if username already exists
        if len(db.execute("SELECT username FROM users WHERE username = ?", request.form.get("username"))) != 0:
            return apology("username already exists", 400)

        # Check if password matches confirmation
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("password must match confirmation", 400)

        # Hash the password before saving
        hashed_password = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, password_hash) VALUES(?, ?)", request.form.get("username"), hashed_password)

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/scoring", methods=["GET", "POST"])
@login_required
def scoring():
    """Display a table of scoring parameters"""
    if request.method == "POST":
        # Restore default values:
        if request.form.get('restore') == "Restore":
            default_stats = {}
            stat_dict = db.execute(f"SELECT name, defaultValue FROM stats")
            for dict in stat_dict:
                default_stats[dict['name']] = dict['defaultValue']

            for stat in default_stats:
                db.execute(f"UPDATE user_stat_values SET {stat} = {default_stats[stat]} WHERE user_id = ?", session["user_id"])
        else:
            return apology("Must type exactly 'Restore' to reset", 400)

        #list of user inputted stats
        user_stats = db.execute("SELECT * FROM user_stat_values WHERE user_id = ?", session["user_id"])[0]
        del user_stats["user_id"]

        # list of possible stats
        stats = db.execute("SELECT * FROM stats")

        # Send user to the homepage
        return render_template("scoring.html", user_stats=user_stats, stats=stats)

    else:
        """Display a table of scoring parameters"""

        # list of default stats
        stats = db.execute("SELECT * FROM stats")

        #list of user inputted stats
        user_stats = db.execute("SELECT * FROM user_stat_values WHERE user_id = ?", session["user_id"])[0]
        del user_stats["user_id"]

        return render_template("scoring.html", user_stats=user_stats, stats=stats)

@app.route("/change_scores", methods=["GET", "POST"])
@login_required
def change_scores():
    if request.method == "POST":
        """Edit fantasy scoring methods"""
        #get list of stat default values for current person
        stats = db.execute("SELECT * FROM user_stat_values WHERE user_id = ?", session["user_id"])[0]
        del stats["user_id"]

        # Ensure input is numeric
        def numeric_check(stat):
            if not request.form.get(stat):
                pass
            else:
                if request.form.get(stat).isnumeric() == False:
                    return apology("must provide numeric values for stats", 400)
        for stat in stats:
            numeric_check(stat)

        # Get all form values
        for stat in stats:
            if not request.form.get(stat):
                pass
            else:
                stats[stat] = request.form.get(stat)

        # Update stat list with new values:
        for stat in stats:
            db.execute(f"UPDATE user_stat_values SET {stat} = {stats[stat]} WHERE user_id = ?", session["user_id"])

        # Send user to the scoreing page
        return redirect("/scoring")

    else:
        """Edit fantasy scoring methods"""
        # list of possible stats
        stats = db.execute("SELECT * FROM stats")

        return render_template("change_scores.html", stats=stats)


@app.route("/teams")
def teams():
    """Display a table of the Nfl teams"""
    # get the nfl_teams
    teams = db.execute("SELECT * FROM nfl_teams ORDER BY team")

    # display the list of teams
    return render_template("teams.html", teams=teams)


@app.route("/2021_season", methods=["GET", "POST"])
@login_required
def season_2021():
    """Display a table of the 2021 Season for given week"""
    if request.method == "POST":
        # Ensure symbol was submitted
        if not request.form.get("week_select"):
            return apology("must provide week", 400)

        week = request.form.get("week_select")

        # get the nfl_teams
        teams = db.execute("SELECT * FROM nfl_teams ORDER BY team")

        # get the games
        games = db.execute("SELECT * FROM season_2021 WHERE week = ? ORDER BY date", week)

        # get the teams' record at this week
        records = {}
        for team in teams:
            # for each team find their number of wins, ties and total competitions (need two wins becasue depending on if team was home or away its win is recorded in a different column)
            ties = db.execute("SELECT COUNT(winner_1) FROM season_2021 WHERE team_id_1 = ? AND week <= ? AND winner_1 = ? AND winner_2 = ? OR team_id_2 = ? AND week <= ? AND winner_1 = ? AND winner_2 = ? ORDER BY date", team['id'], week, 0, 0, team['id'], week, 0, 0)[0]['COUNT(winner_1)']
            wins1 = db.execute("SELECT SUM(winner_1) FROM season_2021 WHERE team_id_1 = ? AND week <= ? ORDER BY date", team['id'], week)[0]['SUM(winner_1)']
            wins2 = db.execute("SELECT SUM(winner_2) FROM season_2021 WHERE team_id_2 = ? AND week <= ? ORDER BY date", team['id'], week)[0]['SUM(winner_2)']
            comps = db.execute("SELECT COUNT(winner_1) FROM season_2021 WHERE team_id_1 = ? AND week <= ? OR team_id_2 = ? AND week <= ? ORDER BY date", team['id'], week, team['id'], week)[0]['COUNT(winner_1)']
            # add up home and away wins to get total wins
            if not wins1:
                wins1 = 0
            if not wins2:
                wins2 = 0
            wins = wins1 + wins2
            # calculate total losses
            losses = comps - wins - ties
            # handle hand team that has a tie
            if ties == 0:
                record = str(wins) + " - " + str(losses)
            else:
                record = str(wins) + " - " + str(losses) + " - " + str(ties)
            # save the team's record to the dictionary
            records[team['id']] = record

        # display updated week of season
        return render_template("2021_season.html", games=games, teams=teams, records=records, week=week)
    else:
        """Display a table of the 2021 Season for week 1 when page first loaded"""
        # get the nfl_teams
        teams = db.execute("SELECT * FROM nfl_teams ORDER BY team")

        # get the games
        games = db.execute("SELECT * FROM season_2021 WHERE week = ? ORDER BY date", "1")

        # get the teams record
        records = {}
        for team in teams:
            # for each team find their number of wins, ties and total competitions (need two wins becasue depending on if team was home or away its win is recorded in a different column)
            ties = db.execute("SELECT COUNT(winner_1) FROM season_2021 WHERE team_id_1 = ? AND week <= ? AND winner_1 = ? AND winner_2 = ? OR team_id_2 = ? AND week <= ? AND winner_1 = ? AND winner_2 = ? ORDER BY date", team['id'], 1, 0, 0, team['id'], 1, 0, 0)[0]['COUNT(winner_1)']
            wins1 = db.execute("SELECT SUM(winner_1) FROM season_2021 WHERE team_id_1 = ? AND week <= ? ORDER BY date", team['id'], 1)[0]['SUM(winner_1)']
            wins2 = db.execute("SELECT SUM(winner_2) FROM season_2021 WHERE team_id_2 = ? AND week <= ? ORDER BY date", team['id'], 1)[0]['SUM(winner_2)']
            comps = db.execute("SELECT COUNT(winner_1) FROM season_2021 WHERE team_id_1 = ? AND week <= ? OR team_id_2 = ? AND week <= ? ORDER BY date", team['id'], 1, team['id'], 1)[0]['COUNT(winner_1)']
            # add up home and away wins to get total wins
            if not wins1:
                wins1 = 0
            if not wins2:
                wins2 = 0
            wins = wins1 + wins2
            # calculate total losses
            losses = comps - wins - ties
            # handle hand team that has a tie
            if ties == 0:
                record = str(wins) + " - " + str(losses)
            else:
                record = str(wins) + " - " + str(losses) + " - " + str(ties)
            # save the team's record to the dictionary
            records[team['id']] = record

        # display week 1 of season
        return render_template("2021_season.html", games=games, teams=teams, records=records, week=1)