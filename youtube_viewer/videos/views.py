from django.shortcuts import render, redirect
from .models import Video
from .forms import VideoForm, ChannelForm
import re
from django.contrib import messages
from django.core.paginator import Paginator
from urllib.parse import urlsplit
import requests

def get_video_id(url):
    video_id = None
    if 'youtu.be' in url:
        path = urlsplit(url).path
        video_id = path.split('/')[-1]
    else:
        match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', url)
        if match:
            video_id = match.group(1)
    return video_id

def video_list(request):
    if request.method == 'POST':
        if 'add_video' in request.POST:
            video_form = VideoForm(request.POST)
            if video_form.is_valid():
                url = video_form.cleaned_data['url']
                video_id = get_video_id(url)
                if video_id:
                    if not Video.objects.filter(video_id=video_id).exists():
                        try:
                            oembed_url = f'https://www.youtube.com/oembed?url={url}&format=json'
                            response = requests.get(oembed_url)
                            response.raise_for_status() # Raise an exception for HTTP errors
                            data = response.json()
                            title = data.get('title', 'Unknown Title')
                            Video.objects.create(video_id=video_id, title=title)
                            messages.success(request, f'Successfully added "{title}".')
                        except requests.exceptions.RequestException as e:
                            messages.error(request, f'Error fetching video title: {e}')
                        except Exception as e:
                            messages.error(request, f'Error adding video: {e}')
                    else:
                        messages.warning(request, 'Video already exists.')
                else:
                    messages.error(request, 'Invalid YouTube URL.')
        elif 'add_channel' in request.POST:
            channel_form = ChannelForm(request.POST)
            if channel_form.is_valid():
                channel_url = channel_form.cleaned_data['channel_url']
                try:
                    # Fetch HTML content of the channel URL
                    response = requests.get(channel_url)
                    response.raise_for_status()
                    html_content = response.text

                    # Extract channel ID from HTML using regex
                    channel_id_match = re.search(r'"externalId":"([a-zA-Z0-9_-]+)"', html_content)
                    if not channel_id_match:
                        raise Exception("Could not find channel ID in the provided URL.")
                    channel_id = channel_id_match.group(1)

                    # Construct uploads playlist URL
                    playlist_id = 'UU' + channel_id[2:]
                    playlist_url = f'https://www.youtube.com/playlist?list={playlist_id}'
                    
                    response = requests.get(playlist_url)
                    response.raise_for_status()
                    html_content = response.text

                    # Find all video URLs in the playlist page
                    video_ids = re.findall(r'"watchEndpoint":{"videoId":"([a-zA-Z0-9_-]{11})"', html_content)
                    video_ids = list(dict.fromkeys(video_ids)) # Remove duplicates

                    videos_added = 0
                    for video_id in video_ids:
                        if not Video.objects.filter(video_id=video_id).exists():
                            try:
                                video_url = f'https://www.youtube.com/watch?v={video_id}'
                                oembed_url = f'https://www.youtube.com/oembed?url={video_url}&format=json'
                                response = requests.get(oembed_url)
                                response.raise_for_status()
                                data = response.json()
                                title = data.get('title', 'Unknown Title')
                                Video.objects.create(video_id=video_id, title=title)
                                videos_added += 1
                            except requests.exceptions.RequestException as e:
                                print(f"Could not fetch title for video {video_id}: {e}")
                                continue
                    
                    messages.success(request, f'Successfully added {videos_added} videos from the channel.')
                except requests.exceptions.RequestException as e:
                    messages.error(request, f'Error fetching channel data: {e}')
                except Exception as e:
                    messages.error(request, f'Error adding channel: {e}')
        return redirect('video_list')
    else:
        video_form = VideoForm()
        channel_form = ChannelForm()
    
    video_list = Video.objects.all()
    paginator = Paginator(video_list, 20) # Show 20 videos per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'videos/video_list.html', {'video_form': video_form, 'channel_form': channel_form, 'videos': page_obj})
