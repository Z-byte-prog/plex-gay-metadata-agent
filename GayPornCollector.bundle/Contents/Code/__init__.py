# Gay Porn Collector
import cookielib, cgi, re, os, json, urllib

PLUGIN_LOG_TITLE='Gay Porn Collector'	# Log Title

VERSION_NO = '2017.03.26.0'

# Delay used when requesting HTML, may be good to have to prevent being
# banned from the site
REQUEST_DELAY = 0

# URLS
BASE_URL='http://www.gayporncollector.com'
BASE_VIDEO_DETAILS_URL=BASE_URL + '%s'

# Example Search URL
# http://www.gayporncollector.com/wp-json/milkshake/v2/pornmovies/?movie_title=%23helix:%20Twink%20Confessions%202
BASE_SEARCH_URL_MOVIES='http://www.gayporncollector.com/wp-json/milkshake/v2/pornmovies/?movie_title='

# http://www.gayporncollector.com/wp-json/milkshake/v2/pornscenes/?scene_title=Wet%20&%20Wild%20With%20Blake%20Mitchell
BASE_SEARCH_URL_SCENES='http://www.gayporncollector.com/wp-json/milkshake/v2/pornscenes/'

#replace # with %27 and ' with %23
def Start():
	HTTP.CacheTime = CACHE_1WEEK
	HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; ' \
        'Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; ' \
        '.NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

class GayPornCollector(Agent.Movies):
	name = 'Gay Porn Collector'
	languages = [Locale.Language.NoLanguage, Locale.Language.English]
	primary_provider = False
	contributes_to = ['com.plexapp.agents.cockporn']

	def Log(self, message, *args):
		if Prefs['debug']:
			Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

	def search(self, results, media, lang, manual):
		self.Log('-----------------------------------------------------------------------')
		self.Log('SEARCH CALLED v.%s', VERSION_NO)
		self.Log("SEARCH - media.title -  %s", media.title)
		self.Log('SEARCH - media.items[0].parts[0].file -  %s', media.items[0].parts[0].file)
		self.Log('SEARCH - media.primary_metadata.title -  %s', media.primary_metadata.title)
		self.Log('SEARCH - media.items -  %s', media.items)
		self.Log('SEARCH - media.filename -  %s', media.filename)
		self.Log('SEARCH - lang -  %s', lang)
		self.Log('SEARCH - manual -  %s', manual)

		if not media.items[0].parts[0].file:
			return

		path_and_file = media.items[0].parts[0].file.lower()
		self.Log('SEARCH - File Path: %s' % path_and_file)

		(file_dir, basename) = os.path.split(os.path.splitext(path_and_file)[0])
		final_dir = os.path.split(file_dir)[1]
		file_name = basename.lower() #Sets string to lower.
		self.Log('SEARCH - File Name: %s', basename)

		search_query_raw = list()
		file_studio = final_dir #used in if statment for studio name
		self.Log('SEARCH - final_dir: %s' % final_dir)
		self.Log('SEARCH - This is a scene: True')
		file_name = re.sub('\(([^\)]+)\)', '', file_name) #Removes anything inside of () and the () themselves.
		file_name = file_name.lstrip(' ') #Removes white spaces on the left end.
		file_name = file_name.lstrip('- ') #Removes white spaces on the left end.
		file_name = file_name.rstrip(' ') #Removes white spaces on the right end.
		self.Log('SEARCH - Split File Name: %s' % file_name.split(' '))
		for piece in file_name.split(' '):
			search_query_raw.append(cgi.escape(piece))

		search_query="%20".join(search_query_raw)
		self.Log('SEARCH - Search Query: %s' % search_query)
		url = BASE_SEARCH_URL_SCENES + '?scene_title=' + search_query
		response = urllib.urlopen(url)
		search_results = json.loads(response.read())
		score=10

		if 'mesage' not in search_results:
			self.Log('SEARCH - results size exact match: %s' % len(search_results))
			for result in search_results:
				try:
					studio = result['related_porn_studio'][0]['porn_studio_name']
					self.Log('SEARCH - studio: %s' % studio)
				except:
					studio = 'empty'
					self.Log('SEARCH - studios: Empty')
				pass
				video_title = result['title']
				video_title = video_title.lstrip(' ') #Removes white spaces on the left end.
				video_title = video_title.rstrip(' ') #Removes white spaces on the right end.
				video_title = video_title.replace(':', '')
				if studio.lower() == file_studio.lower() and video_title.lower() == file_name.lower():
					self.Log('SEARCH - video title: %s' % video_title)
					self.Log('SEARCH - video url: %s' % url)
					self.Log('SEARCH - Exact Match "' + file_name.lower() + '" == "%s"' % video_title.lower())
					self.Log('SEARCH - Studio Match "' + studio.lower() + '" == "%s"' % file_studio.lower())
					results.Append(MetadataSearchResult(id = str(result['ID']), name = video_title, score = 100, lang = lang))
					return

	def update(self, metadata, media, lang, force=False):
		self.Log('UPDATE CALLED')
		enclosing_directory, file_name = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
		file_name = file_name.lower()

		if not media.items[0].parts[0].file:
			return

		file_path = media.items[0].parts[0].file
		self.Log('UPDATE - File Path: %s' % file_path)
		self.Log('UPDATE - metadata.id: %s' % metadata.id)
		url = BASE_SEARCH_URL_SCENES + metadata.id
		# Fetch HTML.
		response = urllib.urlopen(url)
		results = json.loads(response.read())

		# Set tagline to URL.
		metadata.tagline = results['link']
		# Set video title.
		video_title = results['title']
		self.Log('UPDATE - video_title: "%s"' % video_title)

		metadata.title = video_title

		metadata.content_rating = 'X'

		# Try to get and process the director posters.
		valid_image_names = list()
		try:
			i = 0
			video_image_list = results['gallery']
			self.Log('UPDATE - video_image_list: "%s"' % video_image_list)
			coverPrefs = Prefs['cover']
			for image in video_image_list:
				if i != coverPrefs or coverPrefs == "all available":
					poster_url = results['gallery'][i]['guid']
					self.Log('UPDATE - poster_url: "%s"' % poster_url)
					valid_image_names.append(poster_url)
					if poster_url not in metadata.posters:
						try:
							i += 1
							metadata.posters[poster_url]=Proxy.Preview(HTTP.Request(poster_url), sort_order = i)
						except: pass
		except Exception as e:
			self.Log('UPDATE - Error getting posters: %s' % e)
			pass

		# Try to get description text.
		try:
			about_text=results['scene_description']
			self.Log('UPDATE - About Text %s', about_text)
			metadata.summary=about_text
		except Exception as e:
			self.Log('UPDATE - Error getting description text: %s' % e)
			pass

		# Try to get and process the release date.
		try:
			rd=results['release_date']
			self.Log('UPDATE - Release Date: %s' % rd)
			metadata.originally_available_at = Datetime.ParseDate(rd).date()
			metadata.year = metadata.originally_available_at.year
		except Exception as e:
			self.Log('UPDATE - Error getting release date: %s' % e)
			pass

		# Try to get and process the video genres.
		try:
			metadata.genres.clear()
			genres = results['porn_scene_genres']
			self.Log('UPDATE - video_genres count from scene: "%s"' % len(genres))
			self.Log('UPDATE - video_genres from scene: "%s"' % genres)
			for genre in genres:
				metadata.genres.add(genre['name'])
		except Exception as e:
			self.Log('UPDATE - Error getting video genres: %s' % e)
			pass

		# Crew.
		# Try to get and process the director.
#		try:
#			metadata.directors.clear()
#			director = results['director']
#			self.Log('UPDATE - director: "%s"', director)
#			metadata.directors.add(director)
#		except Exception as e:
#			self.Log('UPDATE - Error getting director: %s' % e)
#			pass

		# Try to get and process the video cast.
		try:
			metadata.roles.clear()
			casts = results['related_porn_stars']
			self.Log('UPDATE - cast scene count: "%s"' % len(casts))
			if len(casts) > 0:
				for cast in casts:
					cname = cast['porn_star_name']
					self.Log('UPDATE - cast: "%s"' % cname)
					role = metadata.roles.new()
					role.name = cname
		except Exception as e:
			self.Log('UPDATE - Error getting cast: %s' % e)
			pass

		# Try to get and process the studio name.
		try:
			studio = results['related_porn_studio'][0]['porn_studio_name']
			self.Log('UPDATE - studio: "%s"', studio)
			metadata.studio=studio
		except Exception as e:
			self.Log('UPDATE - Error getting studio name: %s' % e)
			pass

		metadata.posters.validate_keys(valid_image_names)
