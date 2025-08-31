from django import forms

class VideoForm(forms.Form):
    url = forms.URLField(label='YouTube Video URL')

class ChannelForm(forms.Form):
    channel_url = forms.URLField(label='YouTube Channel URL')
