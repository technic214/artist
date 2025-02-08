# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#
from werkzeug.serving import run_simple
from sqlalchemy.sql import func
import os
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from forms import *
from datetime import datetime
# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String(50)))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(
        db.DateTime,
        server_default=func.now(),
        onupdate=func.now())

    def __repr__(self):
        return f'<Vanue {self.id} {self.name}>'


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    def __repr__(self):
        return f'< Artist is {self.name} {self.id}>'


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    start_time = db.Column(db.DateTime, index=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'))

    venue = db.relationship('Venue', backref='shows')
    artist = db.relationship('Artist', backref='shows')

    def __repr__(self):
        return f'<Show {self.id}: {self.name}>'


class Availability(db.Model):

    __tablename__ = 'availability'

    id = db.Column(db.Integer, primary_key=True)
    working_period_start = db.Column(db.DateTime)
    working_period_end = db.Column(db.DateTime)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'))
    artist = db.relationship('Artist', backref='avialabilities')

    def __repr__(self):
        return f'<Availability {self.id}: {self.working_period_start} -> {self.working_period_end}>'


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    try:
        # pagination may be implemented later
        data = Venue.query.order_by(Venue.name).all()
        return render_template('pages/venues.html', areas=data)

    except Exception as e:

        print(f"Error retrieving venues: {e}")
        return render_template('errors/500.html'), 500


@app.route('/venues/search', methods=['GET', 'POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    venues = Venue.query.filter(
        func.lower(
            Venue.name).contains(
            func.lower(search_term))).all()
    current_time = datetime.now()

    response = {
        "count": len(venues),
        "data": [{
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len([
                show for show in venue.shows
                if show.start_time > current_time
            ])
        } for venue in venues]
    }
    print(response)

    return render_template(
        'pages/search_venues.html',
        results=response,
        search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    try:

        data = Venue.query.get(venue_id)
        return render_template('pages/show_venue.html', venue=data)
    except Exception as e:

        print(f"Error retrieving venue with {venue_id} id: {e}")
        return render_template('errors/500.html'), 500


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    venue_form = VenueForm()
    if venue_form.validate():
        try:
            new_venue = Venue(
                name=venue_form.name.data,
                city=venue_form.city.data,
                state=venue_form.state.data,
                address=venue_form.address.data,
                phone=venue_form.phone.data,
                genres=venue_form.genres.data,
                facebook_link=venue_form.facebook_link.data,
                image_link=venue_form.image_link.data,
                website=venue_form.website_link.data
            )
            db.session.add(new_venue)
            db.session.commit()
            flash(
                'Venue ' +
                request.form['name'] +
                ' was successfully listed!')
        except Exception as e:
            db.session.rollback()
            flash(
                'An error occurred. Venue ' +
                request.form['name'] +
                ' could not be listed.')
            print(e)
        finally:
            db.session.close()
    else:
        for field, errors in venue_form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}")

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['POST', 'DELETE'])
def delete_venue(venue_id):
    try:

        item_to_delete = db.session.query(Venue).get(venue_id)

        if not item_to_delete:
            abort(404)

        db.session.delete(item_to_delete)
        db.session.commit()
        flash('Venue successfully deleted!')

    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Error deleting venue: {str(e)}', 'error')
        abort(500)

    return redirect(url_for('shows'))

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    try:

        data = Artist.query.all()
        return render_template('pages/artists.html', artists=data)

    except Exception as e:

        print(f"Error retrieving artists: {e}")
        return render_template('errors/500.html'), 500


@app.route('/artists/search', methods=['POST'])
def search_artists():
    try:

        search_term = request.form['search_term']
        artists = Artist.query.filter(
            Artist.namename.ilike(f'%{search_term}%')).all()
        return render_template(
            'pages/search_artists.html',
            results=artists,
            search_term=request.form.get(
                'search_term',
                ''))

    except Exception as e:

        print(f'Error occured while searchig for specific artist : {e}')
        return render_template('500.html'), 500


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    try:

        data = Show.query.get(artist_id)
        return render_template('pages/show_artist.html', artist=data)

    except Exception as e:

        print('Error occured while retrieving artists:{e}')
        return render_template('500.html'), 500

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    try:

        record = Artist.query.get_or_404(artist_id)
        form = ArtistForm(obj=record)
        return render_template(
            'forms/edit_artist.html',
            form=form,
            artist=record)

    except Exception as e:

        print('Error occured when retrieving artists with error" {e}')
        return render_template('500.html'), 500


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

    record = Artist.query.get_or_404(artist_id)
    form = ArtistForm(obj=record)
    if form.validate():
        try:
            form.populate_obj(record)
            db.session.commit()
            flash(f'Artist {record.name} was updated successfully')
        except Exception as e:
            db.session.rollback()
            flash(f'something went wrong with {record.name}')
        finally:
            db.session.close()
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    record = Venue.query.get_or_404(venue_id)
    form = VenueForm(obj=record)

    return render_template('forms/edit_venue.html', form=form, venue=record)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    form = VenueForm(request.form)

    if form.validate():
        try:
            form.populate_obj(venue)
            db.session.commit()
            flash(f'Venue {venue.id}:{venue.name} was successfully updated!')
        except Exception as e:
            db.session.rollback()
            flash(
                f'The error occurred. Venue {venue.name} could not be updated.')
            print(e)
        finally:
            db.session.close()
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}')

    return redirect(url_for('show_venue', venue_id=venue_id))


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm()
    if form.validate_on_submit():
        try:
            new_artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data
            )
            db.session.add(new_artist)
            db.session.commit()
            flash('Artist ' + new_artist.name + ' was successfully listed!')
        except Exception as e:
            db.session.rollback()
            flash(
                'The error occurred. Artist ' +
                form.name.data +
                ' could not be listed.')
            print(f'Error is {e}')
        finally:
            db.session.close()
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}')

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = db.session.query(Show, Venue, Artist).join(
        Venue).join(Artist).all()
    data = []
    for show, venue, artist in shows:
        data.append({
            "venue_id": venue.id,
            "venue_name": venue.name,
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show.start_time.isoformat()
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()

    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm()
    if form.validate_on_submit():
        try:
            artist = Artist.query.get(form.artist_id.data)
            venue = Venue.query.get(form.venue_id.data)
            if not artist or not venue:
                flash('Invalid artist or venue ID.')
                return render_template('forms/new_show.html', form=form)

            new_show = Show(
                artist_id=artist.id,
                venue_id=venue.id,
                start_time=form.start_time.data
            )
            db.session.add(new_show)
            db.session.commit()
            flash(
                f'Show was successfully listed for {artist.name} at {venue.name}!')
            return redirect(url_for('shows'))
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error creating show: {str(e)}")
            flash('An error occurred. Show could not be listed due to a database issue.')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Unexpected error creating show: {str(e)}")
            flash('An unexpected error occurred. Show could not be listed.')
        finally:
            db.session.close()
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}")
    return render_template('forms/new_show.html', form=form)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
'''
if __name__ == '__main__':
   run_simple('localhost', 0, app, use_reloader=True)


    #app.run(debug=True, port=5000)
'''
# Or specify port manually:

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 63653))
    app.run(host='0.0.0.0', port=port)
