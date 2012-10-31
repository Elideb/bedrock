# coding: utf-8
import re
from operator import itemgetter

from django import forms
from django.conf import settings
from django.forms import widgets
from django.utils.safestring import mark_safe

from captcha.fields import ReCaptchaField
from l10n_utils.dotlang import _
from product_details import product_details

from .email_contribute import INTEREST_CHOICES


FORMATS = (('H', 'HTML'), ('T', 'Text'))
LANGS = settings.NEWSLETTER_LANGUAGES
LANGS_TO_STRIP = ['en-US', 'es']
PARENTHETIC_RE = re.compile(r' \([^)]+\)$')


def strip_parenthetical(lang_name):
    """
    Remove the parenthetical from the end of the language name string.
    """
    return PARENTHETIC_RE.sub('', lang_name, 1)


def get_lang_choices():
    """
     Return a list of choices for language localized for the given locale.
    """
    lang_choices = []
    for lang in LANGS:
        try:
            lang_name = product_details.languages[lang]['native']
        except KeyError:
            continue
        if lang in LANGS_TO_STRIP:
            lang_name = strip_parenthetical(lang_name)
        lang_choices.append([lang, lang_name])
    return sorted(lang_choices, key=itemgetter(1))


class SideRadios(widgets.RadioFieldRenderer):
    """Render radio buttons as labels"""

    def render(self):
        radios = [unicode(w) for idx, w in enumerate(self)]

        return mark_safe(''.join(radios))


class PrivacyWidget(widgets.CheckboxInput):
    """Render a checkbox with privacy text. Lots of pages need this so
    it should be standardized"""

    def render(self, name, value, attrs=None):
        attrs['required'] = 'true'
        input_txt = super(PrivacyWidget, self).render(name, value, attrs)

        policy_txt = _(u'I’m okay with you handling this info as you explain '
                       u'in your <a href="%s">Privacy Policy</a>')
        return mark_safe(
            '<label for="%s" class="privacy-check-label">'
            '%s '
            '<span class="title">%s</span></label>'
            % (attrs['id'], input_txt,
               policy_txt % '/en-US/privacy-policy')
         )


class EmailInput(widgets.TextInput):
    input_type = 'email'

NEWSLETTER_CHOICES = (('app-dev',) * 2,
                      ('mozilla-and-you',) * 2)


class NewsletterForm(forms.Form):
    newsletter = forms.ChoiceField(choices=NEWSLETTER_CHOICES,
                                   widget=forms.HiddenInput)
    email = forms.EmailField(widget=EmailInput(attrs={'required': 'true'}))
    fmt = forms.ChoiceField(widget=forms.RadioSelect(renderer=SideRadios),
                            choices=FORMATS,
                            initial='H')
    privacy = forms.BooleanField(widget=PrivacyWidget)
    source_url = forms.URLField(verify_exists=False, required=False)

    def __init__(self, locale, *args, **kwargs):
        regions = product_details.get_regions(locale)
        regions = sorted(regions.iteritems(), key=lambda x: x[1])
        lang_choices = get_lang_choices()
        lang_initial = locale if locale in LANGS else 'en-US'

        ccode = locale.lower()
        if '-' in ccode:
            ccode = ccode.split('-')[1]

        super(NewsletterForm, self).__init__(*args, **kwargs)
        self.fields['country'] = forms.ChoiceField(choices=regions,
                                                   initial=ccode)
        self.fields['language'] = forms.ChoiceField(choices=lang_choices,
                                                    initial=lang_initial)


class ContributeForm(forms.Form):
    email = forms.EmailField(widget=EmailInput(attrs={'required': 'true'}))
    privacy = forms.BooleanField(widget=PrivacyWidget)
    newsletter = forms.BooleanField(required=False)
    interest = forms.ChoiceField(
        choices=INTEREST_CHOICES,
        widget=forms.Select(attrs={'required': 'true'}))
    comments = forms.CharField(
        widget=forms.widgets.Textarea(attrs={'required': 'true',
                                             'rows': '',
                                             'cols': ''}))
    captcha = ReCaptchaField(attrs={'theme': 'clean'})
