from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect,HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.core.exceptions import *
from django.conf import settings
from django.contrib.sites.models import Site
from facebook.models import *
import time,cgi,urllib
import simplejson as json
		
def login(request):
	verification_code = request.GET.get("code",None)
	args = dict(client_id=settings.APP_ID, callback="http://" + Site.objects.get(id=settings.SITE_ID).domain + request.path)
	if request.GET.get("code",None) != None:
		args["client_secret"] = settings.APP_SECRET
		args["code"] = request.GET.get("code")
		response = cgi.parse_qs(urllib.urlopen(
		"https://graph.facebook.com/oauth/access_token?" +
			urllib.urlencode(args)).read())
		access_token = response["access_token"][-1]
		request.session['access_token'] = access_token
		me_json = urllib.urlopen("https://graph.facebook.com/me?" + urllib.urlencode(dict(access_token=access_token)))
		profile = json.load(me_json)
		user, created = FacebookUser.objects.get_or_create(
		  facebook_id = str(profile["id"]),
		  defaults = {
		    'name': profile["name"],
		    'profile_url': profile["link"]}
		  )
		user.access_token = access_token
		user.save()
		request.session['fb_user'] = str(profile["id"])
		return HttpResponseRedirect(reverse('home'))
	else:
		return HttpResponseRedirect("https://graph.facebook.com/oauth/authorize?" + urllib.urlencode(args))
	
def logout(request):
	request.session.clear()
	return HttpResponseRedirect(reverse('home'))

def home(request):
	access_token = request.session.get('access_token',None)
	fb_user = request.session.get('fb_user',None)
	user_id = request.GET.get('user',None)
	if access_token and fb_user:
		if user_id == None:
			user = FacebookUser.objects.get(facebook_id__iexact=fb_user)
		else:
			user_json = urllib.urlopen("https://graph.facebook.com/" +  user_id +"?" + urllib.urlencode(dict(access_token=access_token)))
			profile = json.load(user_json)
			user = FacebookUser(facebook_id=str(profile["id"]),name=profile["name"], access_token=access_token,profile_url=profile["profile_url"])
			user.save()
		return render_to_response('home.html',{'user': user})
	else:
		return render_to_response('anonymous.html')