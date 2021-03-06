from flask import Flask, render_template, redirect, url_for
from general.basic import spotify_basic_bp
from recommendation.recommendation import recommendation_bp
from database import db
from genre_exploration.flow import genre_explore_bp
from dbdw.flow import dbdw_bp
from nudge.flow import nudge_bp

import os

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)
app.register_blueprint(spotify_basic_bp)
app.register_blueprint(recommendation_bp)
# app.register_blueprint(genre_explore_bp)
app.register_blueprint(nudge_bp)
# app.register_blueprint(dbdw_bp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=True)


@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    return response


