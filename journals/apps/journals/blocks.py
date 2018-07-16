""" Custom blocks """
from django import forms
from django.utils import six
from django.utils.safestring import mark_safe
from wagtail.wagtailcore import blocks
from wagtail.wagtaildocs.blocks import DocumentChooserBlock
from wagtail.wagtailimages.blocks import ImageChooserBlock
from bs4 import BeautifulSoup as parser

from .models import Video
from journals.apps.journals.utils import make_md5_hash

PDF_BLOCK_TYPE = 'pdf'
VIDEO_BLOCK_TYPE = 'xblock_video'
IMAGE_BLOCK_TYPE = 'image'
RICH_TEXT_BLOCK_TYPE = 'rich_text'
RAW_HTML_BLOCK_TYPE = 'raw_html'
STREAM_DATA_TYPE_FIELD = 'type'
STREAM_DATA_DOC_FIELD = 'doc'

SPAN_ID_FORMATTER = '{block_type}-{hash_id}'
BLOCK_FORMATTER = '{span} {block}'


def get_unique_span(block_type, id):
    return '<span id="{}"></span>'.format(SPAN_ID_FORMATTER).format(block_type=block_type, hash_id=make_md5_hash(id))


class VideoChooserBlock(blocks.ChooserBlock):
    """VideoChooserBlock component"""
    target_model = Video
    widget = forms.Select

    class Meta:
        icon = "icon"

    # Return the key value for the select field
    def value_for_form(self, value):
        if isinstance(value, self.target_model):
            return value.pk
        else:
            return value


class PDFBlock(blocks.StructBlock):
    """PDFBlock component"""
    title = blocks.CharBlock()
    doc = DocumentChooserBlock()

    @mark_safe
    def render(self, value, context=None):
        return BLOCK_FORMATTER.format(
            span=get_unique_span(block_type=STREAM_DATA_DOC_FIELD, id=value.get(STREAM_DATA_DOC_FIELD).id),
            block=super(PDFBlock, self).render(value, context)
        )

    def get_searchable_content(self, value):
        return ['Document: ' + value.get('title')]

    class Meta:
        template = 'blocks/pdf.html'


class JournalRichTextBlock(blocks.RichTextBlock):
    """JournalRichTextBlock component"""
    def get_searchable_content(self, value):
        return [parser(value.source, 'html.parser').get_text(' ')]


class JournalRawHTMLBlock(blocks.RawHTMLBlock):
    """JournalRawHTMLBlock component"""
    def value_for_form(self, value):
        """
        Strips dangerous tags from value
        """
        soup = parser(six.text_type(value), 'html.parser')
        forbidden_tags = soup.find_all(["script", "link", "frame", "iframe"])
        for tag in forbidden_tags:
            tag.extract()
        return str(soup)

    def get_searchable_content(self, value):
        return [parser(six.text_type(value), 'html.parser').get_text()]


class XBlockVideoBlock(blocks.StructBlock):
    """XBlockVideoBlock component"""
    BLOCK_TYPE = 'xblock_video'
    STREAM_DATA_FIELD = 'video'

    name = blocks.CharBlock()
    video = VideoChooserBlock(required=True)

    def get_context(self, value, parent_context=None):
        context = super(XBlockVideoBlock, self).get_context(value, parent_context)
        return context

    def get_searchable_content(self, value):
        return ['Video: ' + value.get('name')]

    class Meta:
        template = 'blocks/xblockvideo.html'

    @mark_safe
    def render(self, value, context=None):
        return BLOCK_FORMATTER.format(
            span=get_unique_span(block_type=VIDEO_BLOCK_TYPE, id=value.get('video').id),
            block=super(XBlockVideoBlock, self).render(value, context)
        )


class JournalImageChooserBlock(ImageChooserBlock):
    """ JournalImageChooserBlock component """
    def get_searchable_content(self, value):
        return ['Image: ' + value.title]

    @mark_safe
    def render(self, value, context=None):
        return BLOCK_FORMATTER.format(
            span=get_unique_span(IMAGE_BLOCK_TYPE, value.id),
            block=super(JournalImageChooserBlock, self).render(value, context)
        )
