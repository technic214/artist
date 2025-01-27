#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
migrate = Migrate(app, db)





class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)  # Fixed typo 'geners'
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    lookingfortalent = db.Column(db.Boolean, nullable=False)
    seek = db.Column(db.String(120), nullable=False)

    # Define many-to-many relationship with Artist through the Show model
    shows = db.relationship('Show', back_populates='venue')



    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    lookingforVenue = db.Column(db.Boolean, nullable=False)
    seek = db.Column(db.String(120), nullable=False)

    # Define many-to-many relationship with Venue through the Show model
    shows = db.relationship('Show', back_populates='artist')

class Show(db.Model):
    __tablename__ = 'shows'

    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)

    # Relationships
    venue = db.relationship('Venue', back_populates='shows')
    artist = db.relationship('Artist', back_populates='shows')


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
        date = dateutil.parser.parse(value)  # Parse string into a datetime object
  elif isinstance(value, datetime):
        date = value  # Use the datetime object as-is
  else:
        raise TypeError('Unsupported type for datetime formatting')
    
  if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # Group venues by city and state
    areas = (
        Venue.query
        .with_entities(Venue.city, Venue.state)
        .distinct()
        .all()
    )

    # Structure the data with venues under each area
    data = []
    for area in areas:
        venues_in_area = Venue.query.filter_by(city=area.city, state=area.state).all()
        data.append({
            "city": area.city,
            "state": area.state,
            "venues": [
                {
                    "id": venue.id,
                    "name": venue.name
                } for venue in venues_in_area
            ]
        })

    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_term = request.form.get('search_term', '').strip()
  result = Venue.query.filter( Venue.name.ilike(f"%{search_term}%")).all()
  count = db.session.query(func.count(Venue.id)).filter(Venue.name.ilike(f"%{search_term}%")).scalar()
  print(result)
  # Prepare the response
  response = {
      "count": count,
      "data": []
  }

  # Iterate through the results and prepare the response data
  for venue in result:
      response["data"].append({
         "id":venue.id,
          "name": venue.name,
      })

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)  # Get the venue by ID

    if not venue:  # Handle the case where the venue doesn't exist
        flash(f"Venue with ID {venue_id} not found.")
        return redirect(url_for('venues'))  # Redirect to venues list

    # Query the shows for the venue
    shows = Show.query.filter_by(venue_id=venue_id).join(Artist).all()

    # Separate past and upcoming shows
    past_shows = []
    upcoming_shows = []

    for show in shows:
        show_data = {
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link if show.artist.image_link else 'default_image_url.jpg',
            "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")  # Format datetime
        }
        if show.start_time < datetime.now():
            past_shows.append(show_data)
        else:
            upcoming_shows.append(show_data)

    # Construct the data dictionary
    data = {
        "id": venue.id,
        "name": venue.name,
        "city": venue.city,
        "state": venue.state,
        "address": venue.address,
        "genres": venue.genres.split(',') if venue.genres else [],
        "phone": venue.phone,
        "website_link": venue.website_link,
        "facebook_link": venue.facebook_link,
        "lookingfortalent": venue.lookingfortalent,
        "seek": venue.seek,
        "image_link": venue.image_link if venue.image_link else 'default_image_url.jpg',
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
    new_venue = Venue(
    name=request.form.get('name'),
    city=request.form.get('city'),
    state=request.form.get('state'),
    address=request.form.get('address'),
    phone=request.form.get('phone'),
    genres=','.join(request.form.getlist('genres')),  
    image_link=request.form.get('image_link'),
    facebook_link=request.form.get('facebook_link'),
    website_link = request.form.get('website_link'),
    lookingfortalent=bool(request.form.get('seeking_talent')),  
    seek=request.form.get('seeking_description')
    )

    # Add and commit the new venue to the database
    db.session.add(new_venue)
    db.session.commit()
  # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + request.form['phone'] + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        # Query the venue by id
        venue = Venue.query.get(venue_id)
        
        if not venue:
            return jsonify({"success": False, "error": "Venue not found"}), 404

        # Delete the venue
        db.session.delete(venue)
        db.session.commit()

        # Return success response
        return jsonify({"success": True, "message": f"Venue {venue_id} deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({"success": False, "error": "An error occurred while trying to delete the venue"}), 500
    finally:
        db.session.close()

#  Artists 
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  return render_template('pages/artists.html', artists=Artist.query.order_by('id').all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term =request.form.get('search_term', '')
  result = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
  count = db.session.query(func.count(Artist.id)).filter(Artist.name.ilike(f"%{search_term}%")).scalar()

  response = {
      "count": count,
      "data": []
  }

  for artist in result:
      print("Artist found:", artist.id, artist.name, artist.city)  
      response["data"].append({
          "name": artist.name,
      })
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
 # Query the artist
    artist = Artist.query.get(artist_id)
    if not artist:
        return render_template('errors/404.html'), 404

    # Query the shows for the artist
    shows = Show.query.filter_by(artist_id=artist_id).join(Venue).all()

    # Separate past and upcoming shows
    past_shows = []
    upcoming_shows = []

    for show in shows:
        show_data = {
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")  # Format datetime
        }
        if show.start_time < datetime.now():
            past_shows.append(show_data)
        else:
            upcoming_shows.append(show_data)

    # Add show counts and data to the artist dictionary
    artist_data = {
        "id": artist.id,
        "name": artist.name,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "genres": artist.genres.split(","),
        "image_link": artist.image_link,
        "facebook_link": artist.facebook_link,
        "website_link": artist.website_link,
        "lookingforVenue": artist.lookingforVenue,
        "seek": artist.seek,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=artist_data)




#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # shows the artist page with the given artist_id
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)

  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    try:
        # Retrieve the artist by ID
        artist = Artist.query.get(artist_id)
        
        # If artist doesn't exist, handle gracefully
        if not artist:
            flash(f"Artist with ID {artist_id} not found.")
            return redirect(url_for('index'))

        # Update artist fields with form data
        artist.name = request.form['name']
        artist.genres = ','.join(request.form.getlist('genres'))
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.website_link = request.form['website_link']
        artist.facebook_link = request.form['facebook_link']
        artist.lookingforVenue = bool(request.form.get('seeking_venue'))
        artist.seek = request.form['seeking_description']
        artist.image_link = request.form['image_link']

        # Commit the changes to the database
        db.session.commit()
        flash(f"Artist {artist.name} was successfully updated!")
        return redirect(url_for('show_artist', artist_id=artist_id))

    except Exception as e:
        # Rollback in case of an error
        db.session.rollback()
        print("Error occurred:", e)
        flash(f"An error occurred. Artist {artist_id} could not be updated.")
        return redirect(url_for('show_artist', artist_id=artist_id))
    finally:
        db.session.close()

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # shows the artist page with the given artist_id
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        # Retrieve the artist by ID
        venue = Venue.query.get(venue_id)
        
        # If artist doesn't exist, handle gracefully
        if not venue:
            flash(f"venue with ID {venue_id} not found.")
            return redirect(url_for('index'))

        # Update artist fields with form data
        venue.name = request.form['name']
        venue.genres = ','.join(request.form.getlist('genres'))
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.phone = request.form['phone']
        venue.address = request.form['address']
        venue.website_link = request.form['website_link']
        venue.facebook_link = request.form['facebook_link']
        venue.lookingfortalent = bool(request.form.get('seeking_talent'))
        venue.seek = request.form['seeking_description']
        venue.image_link = request.form['image_link']

        # Commit the changes to the database
        db.session.commit()
        flash(f"Venue {venue.name} was successfully updated!")
        return redirect(url_for('show_venue', venue_id=venue_id))

    except Exception as e:
        # Rollback in case of an error
        db.session.rollback()
        print("Error occurred:", e)
        flash(f"An error occurred. venue {venue_id} could not be updated.")
        return redirect(url_for('show_venue', venue_id=venue_id))
    finally:
        db.session.close()
        return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  new_artist = Artist(
      name=request.form.get('name'),
      city=request.form.get('city'),
      state=request.form.get('state'),
      phone=request.form.get('phone'),
      genres=','.join(request.form.getlist('genres')),  
      image_link=request.form.get('image_link'),
      facebook_link=request.form.get('facebook_link'),
      website_link=request.form.get('website_link'),  # Fixed usage of 'request.form.get'
      lookingforVenue=bool(request.form.get('seeking_venues')),  
      seek=request.form.get('seeking_description')
  )

        
    # Add and commit the new venue to the database
  db.session.add(new_artist)
  db.session.commit()
# on successful db insert, flash success
  flash('Artist ' + request.form['name'] + ' was successfully listed!')
# TODO: on unsuccessful db insert, flash an error instead.
  flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows_data = []
    shows = Show.query.all()
   
    for show in shows:
        print(f"Artist: {show.artist}, Image Link: {show.artist.image_link}")
        shows_data.append({
            "venue_id": show.venue.id,
            "artist_id": show.artist.id,
            "venue_name": show.venue.name,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(show.start_time, format='full')
        })
    return render_template('pages/shows.html', shows=shows_data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    show =Show(
    venue_id=request.form.get('venue_id'),
    artist_id=request.form.get('artist_id'),
    start_time=request.form.get('start_time')
    )

    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback() 
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close() 

  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
