from flask import render_template, Blueprint, session, jsonify, redirect
import pandas as pd
import time as time
import uuid
from recommendation import RecommendationLog
from database import db
from recommendation.recommendation import get_genre_recommendation_by_preference
from recommendation import RecTracks
from dbdw import UserCondition, RecEvent

dbdw_bp = Blueprint('dbdw_bp', __name__, template_folder='templates')


@dbdw_bp.route('/home')
def home():
    return render_template("main.html")


@dbdw_bp.route('/test_url')
def test_url():
    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
    if not user_condition:
        #get the last condition
        last_user_condition = UserCondition.query.order_by(UserCondition.timestamp.asc()).first()

        if last_user_condition:
            user_condition_new = UserCondition(user_id=session["userid"],
                                               timestamp=time.time(),
                                               condition=(last_user_condition.condition+1) % 3)
            db.session.add(user_condition_new)
        else:
            user_condition_new = UserCondition(user_id=session["userid"],
                                               timestamp=time.time(),
                                               condition=0)
            db.session.add(user_condition_new)
        db.session.commit()

    return render_template("form_consent.html")


@dbdw_bp.route('/event_explore')
def event_explore():
    control = 1
    vis = 1
    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()

    print(user_condition.condition)
    return render_template("explore_event.html", control=control, vis=vis, condition=user_condition.condition)


@dbdw_bp.route('/event_recommendation')
def event_recommendation():
    track_df = pd.read_csv("test.csv")

    ts = time.time()
    session['rec_id'] = str(uuid.uuid4())

    recommendation_log = RecommendationLog(id=session['rec_id'],
                                           user_id=session["userid"],
                                           session_id=session['id'],
                                           start_ts=ts)

    db.session.add(recommendation_log)
    db.session.commit()

    recommendations = get_genre_recommendation_by_preference(track_df=track_df, by_preference=True)

    for index, row in recommendations.iterrows():
        rec_tracks = RecTracks(rec_id=session['rec_id'], track_id=row["id"], rank=index)
        db.session.add(rec_tracks)
        db.session.commit()

    tracks = recommendations.merge(track_df[['id', 'event']], on=['id'])

    # create four blocks of list
    l_event = ['classical', 'electronic', 'folk', 'rnb']

    # calculate event recommendation score, valence mean and energy mean
    dict_event_score = {}
    dict_event_valence = {}
    dict_event_energy = {}

    for event in l_event:
        df_event = tracks[tracks["event"] == event]
        dict_event_score[event] = df_event.sum_rank.sum()/len(df_event)
        dict_event_valence[event] = df_event.valence.sum()/len(df_event)
        dict_event_energy[event] = df_event.energy.sum() / len(df_event)

    sorted_dict_event_score = {k: v for k, v in sorted(dict_event_score.items(),
                                                       key=lambda item: item[1],
                                                       reverse=True)}

    dict_return = {}
    for event in sorted_dict_event_score:

        # dictionary for the event
        dict_event = {}

        # attach track attributes
        dict_event["tracks"] = tracks[tracks["event"] == event].to_dict('records')

        # attach availability attributes
        dict_event["availability"] = True

        # attach recommendation score
        dict_event["rec_scores"] = sorted_dict_event_score[event]

        # attach feature attributes
        dict_event["event_valence"] = dict_event_valence[event]
        dict_event["event_energy"] = dict_event_energy[event]

        dict_return[event] = dict_event
        db.session.add(RecEvent(rec_id=session['rec_id'],
                                event_id=event,
                                availability=dict_event["availability"],
                                rec_scores=dict_event["rec_scores"],
                                event_valence=dict_event_valence[event],
                                event_energy=dict_event_energy[event],
                                session_id=session['id'],
                                user_id=session['userid'],
                                timestamp=time.time()
                                ))
    db.session.commit()

    print(dict_return)
    return jsonify(tracks.to_dict('records'))